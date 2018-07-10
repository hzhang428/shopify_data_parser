#!/bin/python
import pandas as pd
import numpy as np
import datetime as dt
import sys
import re
import os
from trie import trie

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class shopify_data_builder:

    def __init__(self, file_name):
        print bcolors.HEADER, "Read in quick books data", bcolors.ENDC
        self.read_in_quick_books_data(file_name)
        print bcolors.OKGREEN, "Success", bcolors.ENDC

        print bcolors.HEADER, "Read in extra tags data", bcolors.ENDC
        self.read_in_extra_tag_data()
        print bcolors.OKGREEN, "Success", bcolors.ENDC

        print bcolors.HEADER, "find family group", bcolors.ENDC
        self.find_family()
        # print self.family
        print bcolors.OKGREEN, "Success", bcolors.ENDC

        print bcolors.HEADER, "Initiate shopify dataframe", bcolors.ENDC
        self.initiate_shopify_df()
        print bcolors.OKGREEN, "Success", bcolors.ENDC

    # reading shopify data and select only needed columns
    def read_in_quick_books_data(self, file_name):
        qb_df_raw = pd.read_csv(file_name)
        self.qb_df = qb_df_raw[[
            'Item',
            'Description',
            'Purchase Description',
            'Quantity On Hand',
            'Preferred Vendor',
            'Price',
            'MOQ',
            'Material',
            'Colour',
            'Family sku',
            'Type1'
        ]]
        self.qb_df = self.qb_df.assign(Done=False)
        # changed sku as the index (this is much more efficient when trying to look for family group)
        self.qb_df.set_index('Item', inplace=True)
        # print self.qb_df

    def read_in_extra_tag_data(self):
        extra_tag_df = pd.read_csv("extra_tag.csv")
        self.extra_tags = {}
        for index, row in extra_tag_df.iterrows():
            self.extra_tags[row['Type']] = row['Extra Tags']
        # print self.extra_tags

    def initiate_shopify_df(self):
        self.shopify_df = pd.read_csv("shopify_data_frame.csv")
        row_num = self.shopify_df.shape[0]
        self.shopify_df.iloc[:row_num] = np.nan
        # print self.shopify_df

    # Find the implicity group member extract the row and index and then mark them as done
    def find_family(self):
        family_list = {}
        search_tree = trie()
        skus = self.qb_df.index.values

        for sku in skus:
            search_tree.insert(sku)
            family_sku = self.qb_df.ix[sku, 'Family sku']
            if pd.notna(family_sku):
                family_list[sku] = family_sku.split(", ")

        for i in skus:
            prefix_i = self.find_family_prefix(i)
            for j in skus:
                prefix_j = self.find_family_prefix(j)
                if i != j and search_tree.find_prefix(prefix_j) and prefix_i == prefix_j:
                    if i not in family_list:
                        family_list[i] = []
                    family_list[i].append(j)
        self.family = family_list
        # print self.family

    def find_family_prefix(self, sku):
        regexs = []
        regexs.append(re.compile(r'^(\w+)-\d+$'))
        regexs.append(re.compile(r'^(\w+)-[A-Z]+$'))
        regexs.append(re.compile(r'^(\w+)-[\w]+$'))
        regexs.append(re.compile(r'^(\d+)[A|B]$'))
        regexs.append(re.compile(r'^(\d+)[L|M|S]$'))

        for r in regexs:
            match = re.findall(r, sku)
            if match:
                return match[0]

    def build_shopify_data(self):
        print bcolors.HEADER, "Building Shopify data"
        print bcolors.OKGREEN,
        i = 0
        for index, row in self.qb_df.iterrows():
            if row['Done'] == True:
                continue
            else:
                self.build_product_data(row, index)
            if i % 20 == 0:
                print ".",
            i += 1
        print bcolors.ENDC
        print bcolors.OKGREEN, "Success", bcolors.ENDC

    # For every product find if they are grouped and then build the data
    def build_product_data(self, row, index):
        if index in self.family:
            self.build_group_product_data(row, index)
            # print index,
        else:
            self.build_iso_product_data(row, index)
            # group = self.find_family()
            # if group:
            #     self.build_group_product_data
            # else:
                # self.build_iso_product_data(row, index)
            
    def build_iso_product_data(self, row, index):
        description = row['Description']
        details = row['Purchase Description']
        # changed sku as the index (this is much more efficient when trying to look for family group)
        sku = index
        color = row['Colour']
        material = row['Material']
        vendor = row['Preferred Vendor']  
        stock_num = int(row['Quantity On Hand'])
        moq_and_weight = row['MOQ'].split('; ')
        min_order_quants = moq_and_weight[0]
        weight = int(moq_and_weight[1].replace('g', ''))
        price = float(row['Price'])
        product_type = row['Type1']
        upc = ""

        std, variants = self.get_variants(min_order_quants)
        handle, title = self.build_handle_and_title(description, sku)
        # print "Handle: ", handle
        # print "Title: ", title
        body_data = { 'SKU' : sku, 'Color' : color, 'Material' : material }
        detail_data = self.build_details(details)
        if 'UPC' in detail_data:
            upc = detail_data['UPC']
            # print upc

        body = self.build_body_html(title, body_data, detail_data)
        # print "Body(html): "
        # print body

        option_1_name = 'Unit'
        option_1_values = self.build_option_1_value(std, variants, price)
        # print "Option 1 Value: ", option_1_values

        # print "Uni Prices: ", price
        prices = self.build_prices(std, variants, price)
        # print "Price: ", prices

        compare_at_prices = self.build_compare_at_prices(std, variants, price)
        # print "Compare_at_prices: ", compare_at_prices

        stocks = self.build_stocks(variants, stock_num)
        # print "Stocks: ", stocks

        weights = self.build_weights(variants, weight)
        # print "Weights", weights

        img_src = self.build_image_src(sku)
        # print img_src

        tags = self.build_tags(title, body_data, detail_data, product_type)
        # print bcolors.OKGREEN + tags + bcolors.ENDC

        l = len(variants)

        product_df = pd.DataFrame({
            'Handle': [handle if i == 0 else np.nan for i in range(0, l)],
            'Title': [title if i == 0 else np.nan for i in range(0, l)],
            'Body (HTML)': [body if i == 0 else np.nan for i in range(0, l)],
            'Vendor': vendor,
            'Type': [product_type if i == 0 else np.nan for i in range(0, l)],
            'Tags': [tags if i == 0 else np.nan for i in range(0, l)],
            'Published': 'TRUE',
            'Option1 Name': [option_1_name if i == 0 else np.nan for i in range(0, l)],
            'Option1 Value': option_1_values,
            'Option2 Name': np.nan,
            'Option2 Value': np.nan,
            'Option3 Name': np.nan,
            'Option3 Value': np.nan,
            'Variant SKU': [sku if i == 0 else np.nan for i in range(0, l)],
            'Variant Grams': weights,
            'Variant Inventory Tracker': 'shopify',
            'Variant Inventory Qty': stocks,
            'Variant Inventory Policy': 'deny',
            'Variant Fulfillment Service': 'manual',
            'Variant Price': prices,
            'Variant Compare At Price': compare_at_prices,
            'Variant Requires Shipping': 'TRUE',
            'Variant Taxable': 'TRUE',
            'Variant Barcode': [upc if i == 0 else np.nan for i in range(0, l)],
            'Image Src': [img_src if i == 0 else np.nan for i in range(0, l)],
            'Image Position': [i for i in range(0, l)],
            'Variant Image': [img_src if i == 0 else np.nan for i in range(0, l)],
            'Variant Weight Unit': 'g'
        })
        self.shopify_df = self.shopify_df.append(product_df, sort=False, ignore_index=True)
        self.qb_df.ix[index, 'Done'] = True

    def build_group_product_data(self, row, index):
        #print self.qb_df.iloc[index]['Family sku']
        pass

    def build_handle_and_title(self, description, sku):
        title = description
        handle = description.replace(' ', '-').replace('"', '').replace('.', '-') + '-' + sku
        return handle, title

    # Some product has details that need to be added to body
    def build_details(self, details):
        e_specs = re.compile(r'\.\.UPC#:(\d+)\.\.')
        e_upc_num = re.compile(r'\.\.Specs:\s?(.*)\.\.')
        e_sizes = re.compile(r'^([^\s]+)')

        specs = re.findall(e_upc_num, details)
        upc_num = re.findall(e_specs, details)
        sizes = re.findall(e_sizes, details)

        detail_data = {}
        if specs:
            detail_data['Specs'] = specs[0]
        if sizes:
            self.build_size(sizes[0], detail_data)
        if upc_num:
            detail_data['UPC'] = upc_num[0]
        return detail_data

    def build_size(self, sizes, detail_data):
        dimention = re.compile("x|X|/").split(sizes)
        l = len(dimention)
        if l < 1:
            return
        detail_data['Length'] = dimention[0]
        if l >= 2:
            detail_data['Width'] = dimention[1]
        if l >= 3:
            detail_data['Height'] = dimention[2]

    # build body data
    def build_body_html(self, title, body_data, detail_data):
        front = '<p><strong>'
        body = front + title + '</strong></p>\r\n'
        for key, value in body_data.iteritems():
            body = body + front + key + ': ' + '</strong>' + value + '</p>\r\n'
        if 'Specs' in detail_data:
            body = body + front + 'Specs' + ': ' + '</strong>' + detail_data['Specs'] + '</p>\r\n'
        if 'Length' in detail_data:
            body = body + front + 'Length' + ': ' + '</strong>' + detail_data['Length'] + '</p>\r\n'
        if 'Width' in detail_data:
            body = body + front + 'Width' + ': ' + '</strong>' + detail_data['Width'] + '</p>\r\n'
        if 'Height' in detail_data:
            body = body + front + 'Height' + ': ' + '</strong>' + detail_data['Height'] + '</p>\r\n'            
        return body

    # Collect as much as data from all the information we have and made tags
    def build_tags(self, title, body_data, detail_data, product_type):
        title_info = title.split(" ")
        body_info = body_data.values()
        detail_info = detail_data.values()
        tags = ", ".join(title_info) + ", " +  ", ".join(body_info) + ", " + ", ".join(detail_info)
        if product_type in self.extra_tags:
            tags = tags + ", " + self.extra_tags[product_type]
        return tags

    def get_variants(self, min_order_quants):
        prog = re.compile(r'(\d+)\((.*)\).*')
        data = re.findall(prog, min_order_quants)
        std = int(data[0][0])
        variants = [int(v) for v in data[0][1].split(', ')]
        return std, variants

    def build_option_1_value(self, std, variants, price):
        unit_prices = self.build_unit_prices(std, variants, price)
        option1 = []
        for i in range(0, len(unit_prices)):
            option1.append('Lot Of ' + str(variants[i]) + ' ($' + str(unit_prices[i]) + ' Each)')
        return option1

    def build_prices(self, std, variants, price):
        prices = [1.18 * price * v if v < std else 1 * price * v if v == std else 0.95 * price * v for v in variants]
        return [round(p, 1) for p in prices]

    def build_unit_prices(self, std, variants, price):
        unit_prices = [1.18 * price if v < std else 1 * price if v == std else 0.95 * price for v in variants]
        return [round(p, 1) for p in unit_prices]

    def build_compare_at_prices(self, std, variants, price):
        compare_at_prices = [np.nan if v < std else 1.18 * price * v for v in variants]
        return [round(p, 1) for p in compare_at_prices]

    def build_stocks(self, variants, stock_num):
        return [int(stock_num / v) for v in variants]

    def build_image_src(self, sku):
        return "https://cdn.shopify.com/s/files/1/1426/4694/products/" + sku + ".jpg"

    # May need to add something in future
    def build_weights(self, variants, weight):
        return [int(v * weight) for v in variants]

    def generate_shopify_data(self):
        self.shopify_df = self.shopify_df.iloc[4:]
        now = dt.datetime.now()
        file_name = 'products_' + str(now.year) + '_' +str(now.month) + '_' + str(now.day) + '.csv'
        path = os.getcwd()
        path += "/shopify_data"
        if not os.path.exists(path):
            os.mkdir(path)
        os.chdir(path)
        self.shopify_df.to_csv(file_name, index=False)
        print bcolors.HEADER, "Shopify data file generated", bcolors.ENDC
        print bcolors.OKGREEN, file_name, bcolors.ENDC


### Main Method ###
def main():
    arg_num = len(sys.argv)
    if arg_num != 2:
        raise Exception('Argument is not correct')

    data_builder = shopify_data_builder(sys.argv[1])
    data_builder.build_shopify_data()
    data_builder.generate_shopify_data()
    # print data_builder.qb_df


if __name__ == "__main__": main()
