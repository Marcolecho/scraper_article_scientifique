import os
from websiteToScrap.scraperMDPI import getPDF_MDPI
from websiteToScrap.scraperSCIENCEDIRECT import getPDF_SCIENCEDIRECT
from websiteToScrap.scraperWILEY import getPDF_WILEY
from websiteToScrap.scraperFRONTIERS import getPDF_FRONTIERS
from websiteToScrap.scraperSPRINGER import getPDF_SPRINGER
from websiteToScrap.scraperPUBSACS import getPDF_PUBSACS
from websiteToScrap.scraperPUBSRSC import getPDF_PUBSRSC
from searchInPDF import searchInPDF
from markdown_pdf import MarkdownPdf, Section

download_folder_Web = "C:/Users/marct/Downloads"



# Data pour extraction Cellulose (à décommenter et commenter les autres)
validRecherche = [[" cellulose"], ["dissolution", "dissolute", "dissolutive", "dissolving", "dissolved"],  ["deep eutectic solvent",  "DES"]]
rapportScraping = "./report/rapportCellulose.md"
rapportScrapingPDF = "./report/rapportCellulose.pdf"
listFolders = [
    "D:/dataStageLabo/cellulose/pdf_MDPI_cellulose",
    "D:/dataStageLabo/cellulose/pdf_SCIENCEDIRECT_cellulose",
    "D:/dataStageLabo/cellulose/pdf_WILEY_cellulose",
    "D:/dataStageLabo/cellulose/pdf_FRONTIERS_cellulose",
    "D:/dataStageLabo/cellulose/pdf_SPRINGER_cellulose",
    "D:/dataStageLabo/cellulose/pdf_PUBSACS_cellulose",
    "D:/dataStageLabo/cellulose/pdf_PUBSRSC_cellulose",
    ]


"""
# Data pour extraction chitin (à décommenter et commenter les autres)
validRecherche = [[" chitin"], ["dissolution", "dissolute", "dissolutive", "dissolving", "dissolved"],  ["deep eutectic solvent",  "DES"]]
rapportScraping = "./report/rapportChitin.md"
rapportScrapingPDF = "./report/rapportChitin.pdf"
listFolders = [
    "D:/dataStageLabo/chitin/pdf_MDPI_chitin",
    "D:/dataStageLabo/chitin/pdf_SCIENCEDIRECT_chitin",
    "D:/dataStageLabo/chitin/pdf_WILEY_chitin",
    "D:/dataStageLabo/chitin/pdf_FRONTIERS_chitin",
    "D:/dataStageLabo/chitin/pdf_SPRINGER_chitin",
    "D:/dataStageLabo/chitin/pdf_PUBSACS_chitin",
    "D:/dataStageLabo/chitin/pdf_PUBSRSC_chitin",
    ]
"""
"""
# Data pour extraction Silk (à décommenter et commenter les autres)
validRecherche = [[" silk"], ["dissolution", "dissolute", "dissolutive", "dissolving", "dissolved"],  ["deep eutectic solvent",  "DES"]]
rapportScraping = "./report/rapportSilk.md"
rapportScrapingPDF = "./report/rapportSilk.pdf"
listFolders = [
    "D:/dataStageLabo/silk/pdf_MDPI_silk",
    "D:/dataStageLabo/silk/pdf_SCIENCEDIRECT_silk",
    "D:/dataStageLabo/silk/pdf_WILEY_silk",
    "D:/dataStageLabo/silk/pdf_FRONTIERS_silk",
    "D:/dataStageLabo/silk/pdf_SPRINGER_silk",
    "D:/dataStageLabo/silk/pdf_PUBSACS_silk",
    "D:/dataStageLabo/silk/pdf_PUBSRSC_silk",
    ]
"""

# Récupération des premiers mots de pour chaque groupe de mot
motRecherche = []
listWord = []
for i in validRecherche:
    motRecherche.append(i[0])
    for j in i:
        listWord.append(j) 

# Caratère de début de phrase donnant si la ligne commençant par un des caractères doit être supprimé car inutile
listRemover = ("#", "*", "_", ">", "fig")

# Dossier de téléchargement base pour ensuite les transférer dans les dossiers de stockage
os.makedirs(download_folder_Web, exist_ok=True)

download_folder_MDPI = listFolders[0]
download_folder_SCIENCEDIRECT = listFolders[1]
download_folder_WILEY = listFolders[2]
download_folder_FRONTIERS = listFolders[3]
download_folder_SPRINGER = listFolders[4]
download_folder_PUBSACS = listFolders[5]
download_folder_PUBSRSC = listFolders[6]

for folder in listFolders:
    os.makedirs(folder, exist_ok=True)


"""
Lancement des différents scrapper qui vont récupérer les pdfs qui nous interesse par rapport à la recherche dans les mots de "validRecherche"
on récupère aussi la liste des noms d'articles si ça peut servir

On nettoie le fichier de rapport et on lance la recherche dans les pdf pour récupérer les informations utile et l'écrire dans 
"""
if __name__ == "__main__":
    globalTitles = []
    """
    print("==============================SCIENCEDIRECT==============================")
    titles = getPDF_SCIENCEDIRECT(download_folder_Web, download_folder_SCIENCEDIRECT, motRecherche, validRecherche)    
    globalTitles.extend(titles)
    
    print("==============================WILEY==============================")
    titles = getPDF_WILEY(download_folder_WILEY, motRecherche, validRecherche)                               
    globalTitles.extend(titles)
    
    print("==============================PUBSACS==============================")
    titles = getPDF_PUBSACS(download_folder_Web, download_folder_PUBSACS, motRecherche, validRecherche)      
    globalTitles.extend(titles)

    print("==============================PUBSRSC==============================")
    titles = getPDF_PUBSRSC(download_folder_Web, download_folder_PUBSRSC, motRecherche, validRecherche)      
    globalTitles.extend(titles)
    
    print("==============================FRONTIERS==============================")
    titles = getPDF_FRONTIERS(download_folder_Web, download_folder_FRONTIERS, motRecherche, validRecherche)  
    globalTitles.extend(titles)

    print("==============================SPRINGER==============================")
    titles = getPDF_SPRINGER(download_folder_Web, download_folder_SPRINGER, motRecherche, validRecherche)    
    globalTitles.extend(titles)
    
    print("==============================MDPI==============================")
    titles = getPDF_MDPI(download_folder_Web, download_folder_MDPI, motRecherche, validRecherche)                                 
    globalTitles.extend(titles)
    
    print(globalTitles)
    """
    
    # pour ne faire que le scrapping, commenter les lignes suivantes, elles servent à l'exploitation des pdfs
    with open(rapportScraping, "w", encoding="utf-8") as fichier:
        fichier.write("")

    searchInPDF(listFolders, listRemover, listWord, rapportScraping)
    
    pdf = MarkdownPdf()
    with open(rapportScraping, "r", encoding="utf-8") as f:
        contenu_md = f.read()
    pdf.add_section(Section(contenu_md))
    pdf.save(rapportScrapingPDF)
