from tokenizer import TokenCatalog

class Lexer:

    def GetGrabageItems() -> list:
        return [
            " ", "\n"
        ]

    def SeparateStrings(text : str):

        current = ''
        s = 0

        saveTable = []

        for i, char in enumerate(text):
            if char in ["'", '"']:
                if char == current:
                    saveTable = [text[s:i]]
                    text[s:i] = ""
                    current = ''
                elif current == '':
                    current = char

        if current != '': raise Exception("String is not ended.")
        return text, saveTable


    def GetCharacterType(char : str) -> int:
        if char.isalpha():
            return 0
        elif char.isnumeric():
            return 1
        return 2
        

    def Separate(text : str) -> list: #separates text by character type
        result = [""]
        ind = 0

        for i, char in enumerate(text):
            if Lexer.GetCharacterType(text[i-1]) != Lexer.GetCharacterType(char) or Lexer.GetCharacterType(char) == 2:
                if not (text[i-1] == "-" and Lexer.GetCharacterType(char) == 1):
                    ind+=1
                    result += [""]

            result[ind] += char

        for i, element in enumerate(result): #clean up
            if element == "": result.pop(i) 

        return result
    
    def Bond(elements : list) -> list:
        keywords = TokenCatalog.GetAllKeywords()
        special = []
        
        for keyword in keywords:
            if len(keyword) > 1 and Lexer.GetCharacterType(keyword) == 2:
                special += [keyword]


        for keyword in special:
            for j, item in enumerate(elements):
                chunk = len(keyword) + j
                guess = ''.join(elements[j:chunk])
                if guess == keyword:
                    for l in range(j+1, chunk):
                        elements.pop(l)
                    elements[j] = guess
        
        return elements
    
    def Clean(elements : list) -> list:
        result = []
        garbage = Lexer.GetGrabageItems()

        for item in elements:
            if not item in garbage: result += [item]

        return result
                    
            


        
        

        

