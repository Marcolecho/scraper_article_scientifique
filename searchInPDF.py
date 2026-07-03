import os
import time 
import pymupdf4llm
import re

"""
choix de la techno de la lecture de PDF : 
https://onlyoneaman.medium.com/i-tested-7-python-pdf-extractors-so-you-dont-have-to-2025-edition-c88013922257 
"""


"""
Fonction qui pour une chaine de caractère donnée, va chercher une correcpondance dans le texte.
Si il existe une correspondance, supprime ce qu'il y a après la correspondance

params : 
* markdown_text : fichier pdf à traiter sous forme de chaine de caractère (en .md / markdown)
* pattern : chaine de caractère à chercher dans le texte
"""
def cutAfterPattern(markdown_text, pattern):
    if pattern in markdown_text:
        markdown_propre = markdown_text.split(pattern)[0]
        return markdown_propre
    return markdown_text


"""
Fonction qui va chercher le doi afin de l'utiliser en tant que titre

params : 
* markdown_text : fichier pdf à traiter sous forme de chaine de caractère (en .md / markdown)
"""
def deletePicture(markdown_text):
    pattern = r"\*\*==> picture \[.*?\] intentionally omitted <==\*\*"
    texte_propre = re.sub(pattern, "", markdown_text, flags=re.DOTALL)
    return texte_propre



"""
Fonction qui va supprimer toutes les images non traités par le lecteur de pdf (les images sont transformés en texte avec le lecteur)

params : 
* markdown_text : fichier pdf à traiter sous forme de chaine de caractère (en .md / markdown)
"""
def extraire_patterns_doi(markdown_text):
    pattern_doi = r"10\.\d{4,9}/[-._;()/:A-Z0-9]+"
    dois = re.findall(pattern_doi, markdown_text, re.IGNORECASE)
    return dois[0]


"""
On coupe le texte en bloc de lignes 
Si la ligne commence par un des caractère dans la liste des listRemover, on ne prend pas la ligne en compte
On retourne les lignes nettoyé

params : 
* markdown_text : fichier pdf à traiter sous forme de chaine de caractère (en .md / markdown)
* listRemover : liste des premiers caractères de ligne à supprimer
"""
def readLinePerLine(markdown_text, listRemover): 
    lines = markdown_text.splitlines()
    interestingLines = []
    for line in lines:
        line = line.lower() 
        if not line.strip().startswith(listRemover) and len(line) > 10 and line.strip():
            interestingLines.append(line)

    return extractInterrestingText(interestingLines)


"""
On cherche ici les éléments qui nous interresse dans listPatternSelector et dans pattern qui permet de detecter un ratio (1:2)
Pour chaque bloc de lignes, si il y a au moins un mot dans la liste de listPatternSelector et un ratio
    alors on prend le bloc de ligne + le bloc d'avant et après au cas où
à la fin quand on a tout nos blocs, on 

params : 
* interestingLines : listes de blocs de lignes ne commençant pas par les caractères de listRemover
"""
def extractInterrestingText(interestingLines):
    pattern = r"(\b\d+(?:\s*:\s*\d+){1,2})\b[\s()]"
    listPatternSelector = ("molar ratio", "M ratio", "wt%", "ratio")
    lenInterestingLine = len(interestingLines)
    textsInterresting = []
    for index, line in enumerate(interestingLines):
        text = ""
        if any(mot in line for mot in listPatternSelector):
            ratios_trouves = re.search(pattern, line, re.IGNORECASE)
            if(ratios_trouves):
                if(index > 0):
                    text += interestingLines[index-1]
                text += line
                if(index < lenInterestingLine):
                    text += interestingLines[index+1]
                
                textsInterresting.append(text)
    return extractLimitText(textsInterresting, pattern)



"""
Pour chaque bloc de lignes, on découpe en phrase
    pour chaque phrase si il y a un ratio ou un %, on prend en compte cette ligne et on créer un compteur de 10 phrase
        Si la prochaine phrase ne contient pas de ratio ou %, on prend quand même en compte jusqu'a 10 phrase de plus
        Si toujours rien, on stoppe et on récupère les phrases
        Si sur les 10 lignes suivantes on trouve en ratio ou %, on recommence le compteur à 10 à partir de la phrase qui à le ratio ou %

        Une fois le compteur de 10 phrases ou le bloc terminé on stocke le résultat pure dans une liste

        Une fois fini, on vérifie qu'il n'y a pas de texte pure en doublon ce qui peut arrivers car dans "extractInterrestingText", 
        on prend le bloc de texte avant et après 

params : 
* textsInterresting : listes de blocs de lignes ne commençant pas par les caractères de listRemover et ayant des infos pertinentes 
* pattern : permet de detecter un ratio (1:2)
"""
def extractLimitText(textsInterresting, pattern):
    listInterrestingText = []
    for text in textsInterresting:
        limitAccepter = 10
        actualLimit = 0 
        asfoundonePatern = False
        interrestingText = ""
        text = text.split(".")
        for index, phrase in enumerate(text):
            ratios_trouve = re.search(pattern, phrase, re.IGNORECASE)
            if ratios_trouve or "%" in phrase:
                if asfoundonePatern == False:
                    if(not index == 0): 
                        interrestingText = text[index-1]
                    asfoundonePatern = True
                actualLimit = 0
                interrestingText += phrase + "."
                time.sleep(1)
            else:
                if(asfoundonePatern):
                    if(actualLimit > limitAccepter):
                        break
                    actualLimit += 1 
                    interrestingText += phrase + "."
        listInterrestingText.append(interrestingText)

    listInterrestingText.sort()
    
    listCleanedText = []
    n = len(listInterrestingText)
    
    for i in range(n):
        if i == n - 1:
            listCleanedText.append(listInterrestingText[i])
            continue
            
        texte_actuel = listInterrestingText[i]
        texte_suivant = listInterrestingText[i+1]

        texte_actuel_trim = texte_actuel[:30]
        
        if texte_suivant.startswith(texte_actuel_trim):
            print(f"[Nettoyage] Doublon détecté. Suppression de la version courte : '{texte_actuel[:30]}...'")
            continue
        else:
            listCleanedText.append(texte_actuel)
            
    return listCleanedText


"""
On récupère les tableaux dans le pdf en texte
On renvoie le texte sans les tableaux

params : 
* markdown_text : fichier pdf à traiter sous forme de chaine de caractère (en .md / markdown)
"""
def extractArray(markdown_text):
    """
    1. \*?\*? -> Capture les éventuelles étoiles du gras (**) si elles existent
    2. (?:table|t\s*a\s*b\s*l\s*e)\s+\d+ -> Trouve le "Table X"
    3. (?:(?!(?:table|t\s*a\s*b\s*l\s*e)\s+\d+)[\s\S])*? -> avant tant qu'il ne rencontre pas un AUTRE "Table X"
    4. (?:\n\|.*\|)+ -> Capture le tableau Markdown
    """
    pattern = r"(\*?\*?(?:table|t\s*a\s*b\s*l\s*e)\s+\d+(?:(?!(?:table|t\s*a\s*b\s*l\s*e)\s+\d+)[\s\S])*?(?:\n\|.*\|)+)"
    
    listTables = re.findall(pattern, markdown_text, flags=re.IGNORECASE)
    texte_withoutTable = re.sub(pattern, "", markdown_text, flags=re.IGNORECASE)
    texte_withoutTable = re.sub(r'\n{3,}', '\n\n', texte_withoutTable)
    
    return listTables, texte_withoutTable


"""
Pour chaque tableau, regarde le titre du tableau, si il y au moins un mot dans la liste listWord qui correspond, 
on regarde le titre des colonnes. Si il y a au moins une colonne qui correspond à la liste listWord
    On garde le tableau
On renvoie tout les tabeaux pertinents

params : 
* listTables : liste des tableaux du pdf 
* listWord : liste des mots pertinents à utiliser pour voir si le tableau nous interesse 
* arrayNameColumn : liste de mots à utiliser pour séparer les tableaux intéressant des tableaux inutiles dans notre cadre
"""
def filterArray(listTables, listWord, arrayNameColumn):
    listAcceptableTable = []
    for table in listTables:
        tableSplit = (table.split('|', 1))
        tableTitle = tableSplit[0]
        tableData = tableSplit[1]
        if any(mot in tableTitle for mot in tuple(listWord)):
            data = (tableData.split('|---|', 1))
            columnTitle = (data[0]).lower()
            columnTitle = columnTitle.replace("<br>"," ")
            columnTitle = columnTitle.replace("**","")
            if any(mot in columnTitle for mot in arrayNameColumn):
                listAcceptableTable.append(table)
    return listAcceptableTable
    
"""
params : 
* file : fichier pdf à traiter
* listRemover : liste des premiers caractères de ligne à supprimer
* listWord : liste des mots de recherche
* arrayNameColumn : liste de mots à utiliser pour séparer les tableaux intéressant des tableaux inutiles dans notre cadre
* rapportScraping : chemin du fichier rapport où l'on écrit les résultats 
"""
def readFile(file, listRemover, listWord, arrayNameColumn, rapportScraping):

    # Suppression de la section Référence afin d'avoir moins de données à traiter ainsi que les images
    markdown = pymupdf4llm.to_markdown(file)
    markdown = cutAfterPattern(markdown, "## REFERENCES")
    markdown = cutAfterPattern(markdown, "## References")
    markdown = cutAfterPattern(markdown, "## **References**")
    markdown = cutAfterPattern(markdown, "## **REFERENCES**")
    markdown = deletePicture(markdown)

    # Ouvre le fichier en écriture à la suite  
    with open(rapportScraping, "a", encoding="utf-8") as fichier:

        # écrit le doi comme titre 
        fichier.write(f"# {extraire_patterns_doi(markdown)} \n\n")

        print(f"debut extraction {file}")

        # extrait et récupère les tableaux interressant par rapport à nos besoins
        listTables, markdownMinTable = extractArray(markdown)
        listAcceptableTable = filterArray(listTables, listWord, arrayNameColumn)

        # écrit pour chaque tableau ces derniers dans le fichier
        fichier.write(f"## Tableaux\n\n")
        for table in listAcceptableTable:
            fichier.write(f"{table}\n\n<br>\n\n")

        print(f"fin extraction tableaux {file}")

        # Récupère les passages de textes intéressant et les écrit dans le fichier 
        listTexts = readLinePerLine(markdownMinTable, listRemover)
        fichier.write(f"## Textes\n\n")
        for text in listTexts:
            fichier.write(f"```\n{text}\n```\n\n")

        print(f"fin extraction textes {file}")
   
        fichier.write(f"\n\n<br><br>\n\n")


"""
Fonction point d'entrée

Va récupérer dans chaque dossier, tout les pdfs et lance pour chaque, la lecture de ces derniers "readFile"

params : 
* listFolder : la liste des dossiers contenant les pdf
* listRemover : liste des premiers caractères de ligne à supprimer
* listWord : liste des mots de recherche
* rapportScraping : chemin du fichier rapport où l'on écrit les résultats 
"""
def searchInPDF(listFolder, listRemover, listWord, rapportScraping):
    arrayNameColumn = ("des", "molar", "hba", "hbd", "dissolution", "solubility")
    for folder in listFolder:
        files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        for file in files:
            readFile(folder + '/' + file, listRemover, listWord, arrayNameColumn, rapportScraping)