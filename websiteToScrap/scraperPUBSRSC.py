import base64
import math
import os
import time
import re
import shutil
import zipfile
from datetime import datetime
from botasaurus.browser import browser, Driver



"""
Accède à la page web et récupère le nombre de page max
Pour chaque page : 
    récupère les articles et les télécharge si il y a au moins un résultat 
    si pas d'articles dans la page on stop
"""
@browser(
    headless=False,           # Obligatoire pour voir l'écran et passer les bots
    block_images_and_css=False, 
    reuse_driver=True
)
def run_browser_scraping(driver: Driver, data): 
    goToNextPage(driver, data, 1)
    pageMax = getPageMax(driver)
    articles = []
    for i in range(2, pageMax):
        
        listTitles, listAll = getArticles(driver, data)
        if len(listTitles) == 0: return articles
        articles.extend(listTitles)
        downloadArticles(driver, data, listAll)
        goToNextPage(driver, data, i)
    
    return articles
    
"""
Navigue sur la page suivante en modifiant l'url avec le nouveau nombre de page
"""
def goToNextPage(driver, data, page):
    domain = data["domain"]
    query = data["query"] 
    driver.google_get(f"{domain}/search-results?page={page}&q={query}&access_unlocked=true&access_openaccess=true&access_free=true") 
    time.sleep(10)



"""
Récupération du nombre de pages maximum
""" 
def getPageMax(driver: Driver):
    elem = driver.select("div[data-total-item-count]")
    elem = elem.get_attribute("data-total-item-count")
    return int(elem)



"""
Télécharge les fichiers qui se télécharge automatiquement dans le dossier "download"
Regarde avant et apres dans le dossier telechargement pour voir les différences 
Pour les nouveaux fichiers, déplace dans le dossier prévu 

params : 
* listToDownload : liste d'article à télécharger
"""
def downloadArticles(driver, data, listToDownload): 
    for art in listToDownload:
        driver.google_get(art["url"])
        time.sleep(6) 
        
        js_script = """
        return fetch(window.location.href)
            .then(response => response.blob())
            .then(blob => new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onloadend = () => resolve(reader.result.split(',')[1]);
                reader.onerror = reject;
                reader.readAsDataURL(blob);
            }));
        """
        pdf_base64 = driver.run_js(js_script)
        
        if(pdf_base64):
            nom_fichier = f"article_{int(time.time())}.pdf"
            chemin_final = os.path.join(data["download_folder"], nom_fichier)
            
            with open(chemin_final, "wb") as f:
                f.write(base64.b64decode(pdf_base64))

            print(f"Article téléchargé : {art['titre']}") 
        else:
            print(f"Erreur, impossible de télécharger l'article : {art['titre']}") 
        time.sleep(4)



"""
Récupère les titres des articles de la page
Pour chaque titre 
    si le titre contient tout les mots de la recherxhe
    On récupère des éléments pour reconstruire le lien PDF et on l'ajoute à la liste des articles à télécharger
    On renvoie les noms d'articles et les liens de téléchargement 
"""
def getArticles(driver, data):
    listTitles = []
    listAll = []
    articles = driver.select_all("div.item-info")
    
    for article in articles:
        articleTitle = article.select("h4")
        articleTitle= article.select("a")
        title = (articleTitle.text).lower()

        isValid = True
        for listMotsVarValid in data["validRecherche"]:   
            isAtLeastOneValid = False
            for motVarValid in listMotsVarValid:
                if motVarValid in title: 
                    isAtLeastOneValid = True
                    break

            if isAtLeastOneValid == False: 
                isValid = False
                break
        if(isValid == True):
            pdfLink = article.select("a.al-link.pdf.openInAnotherWindow.stats-item-pdf-download.js-download-file-gtm-datalayer-event.sri-attachment.solr-pdfaccess.js-single-pdf-link")
            viewPdf = article.select("a.viewArticleLink")
            hrefArt = pdfLink.href
            viewPdf = viewPdf.href

            viewPdf = viewPdf.replace("article","article-pdf")
            viewPdf = viewPdf.split("/")
            viewPdf.pop()
            hrefArt = hrefArt.split('/')[-1]

            linkDownload = data["domain"] + '/'.join(viewPdf) + '/' + hrefArt
            print(linkDownload) 
            listTitles.append(title)
            listAll.append({
                "titre": title,
                "url": linkDownload
            })

            print("fichier à télécharger : ", title)

    return listTitles, listAll

"""
Point d'entrée du fichier

Contruit la query (les mots de la recherche à mettre dans l'URL)
Contruit un object contenant toutes les informations importantes
Lance le scraping avec run_browser_scraping
renvoie le nom des pdf trouvés

params : 
* source_folder : Dossier dans lequel les fichiers sont téléchargés avant d'être déplacé dans download_folder 
* download_folder : Dossier dans lequel poser les pdf
* motRecherche : les mots de la recherche à taper dans les sites
* validRecherche : les mots valides si trouvé
"""
def getPDF_PUBSRSC(source_folder, download_folder, motRecherche, validRecherche):
    query = "%20".join(motRecherche)
    domain = f"https://pubs.rsc.org"
    donnees = {
        "motRecherche": motRecherche,
        "domain": domain,
        "download_folder": download_folder,
        "source_folder": source_folder,
        "query": query,
        "validRecherche": validRecherche
    }   
    
    print("Démarrage du processus Botasaurus...")
    listArticles = run_browser_scraping(data=donnees)
    run_browser_scraping.close()
    return listArticles






