# import re

class trie_node:
    def __init__(self):
        self.has_word = False
        self.child = {}
        self.word = ""

class trie:
    def __init__(self):
        self.node = trie_node()

    def insert(self, word):
        if word == None or word == "" or len(word) < 1:
            return
        node = self.node
        for i in range(0, len(word)):
            letter = word[i]
            if letter not in node.child:  
                node.child[letter] = trie_node()
            node = node.child[letter]
        node.has_word = True
        node.word = word

    def find_node(self, word):
        if word == None or word == "" or len(word) < 1:
            return None
        node = self.node
        for i in range(0, len(word)):
            letter = word[i]
            if letter in node.child:
                node = node.child[letter]
            else:
                return None
        return node
    
    def find_prefix(self, prefix):
        if self.find_node(prefix) == None:
            return False
        else:
            return True

    def find_word(self, word):
        node = self.find_node(word)
        if node.has_word:
            return True
        else:
            return False


# def main():
#     tree = trie()
#     family = {}
#     data = ['GB0066-50', 'GB0066-63', 'GB0066-76', 'GB0066-89', 'GB0066-100', '15010202A', '15010202B', 'GL0025-IVO', 'GL0025-WHT', 'GB0204-36Y', 'GB0204-36AM', '15010841L', '15010841M', '15010841S']
#     for d in data:
#         tree.insert(d)

#     for i in data:
#         prefix_i = find_family_prefix(i)
#         for j in data:
#             prefix_j = find_family_prefix(j)
#             if i != j and tree.find_prefix(prefix_j) and prefix_i == prefix_j:
#                 if i not in family:
#                     family[i] = []
#                 family[i].append(j)
    
#     print family
#     # print tree.find_prefix('GB0066'), 1
#     # print tree.find_prefix('GB0204'), 2
#     # print tree.find_prefix('15010202'), 3
#     # print tree.find_prefix('15010841'), 4
#     # print tree.find_prefix('GL0025'), 5
#     # print tree.find_prefix('GB0204'), 6
#     # print tree.find_word('GB0066-50'), 7
#     # print tree.find_word('GB0066-63'), 8
#     # print tree.find_word('GB0066-76'), 9
#     # print tree.find_word('GB0066-89'), 10
#     # print tree.find_word('GB0066-100'), 11
#     # print tree.find_word('GB0204-36Y'), 12
#     # print tree.find_word('GB0204-36AM'), 13
#     # print tree.find_word('15010202A'), 14
#     # print tree.find_word('15010202B'), 15
#     # print tree.find_word('GL0025-IVO'), 16
#     # print tree.find_word('GL0025-WHT'), 17
#     # print tree.find_word('GB0204-36Y'), 18
#     # print tree.find_word('GB0204-36AM'), 19
#     # print tree.find_word('15010841L'), 20
#     # print tree.find_word('15010841M'), 21
#     # print tree.find_word('15010841S'), 22

# def find_family_prefix(sku):
#     regexs = []
#     regexs.append(re.compile(r'^(\w+)-\d+$'))
#     regexs.append(re.compile(r'^(\w+)-[A-Z]+$'))
#     regexs.append(re.compile(r'^(\w+)-[\w]+$'))
#     regexs.append(re.compile(r'^(\d+)[A|B]$'))
#     regexs.append(re.compile(r'^(\d+)[L|M|S]$'))

#     for r in regexs:
#         match = re.findall(r, sku)
#         if match:
#             return match[0]

# if __name__ == "__main__":main()

