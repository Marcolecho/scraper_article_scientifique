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
Accède à la page web et valide le bouton des cookies
Scroll vers le bas pour charger les articles
récupère les articles et les télécharge si il y a au moins un résultat 
"""
@browser(
    headless=False,           # Obligatoire pour voir l'écran et passer les bots
    block_images_and_css=False, 
    reuse_driver=True
)
def run_browser_scraping(driver: Driver, data): 
    domain = data["domain"]
    query = data["query"]
    driver.google_get(f"{domain}/search?query={query}&tab=articles&origin=https%3A%2F%2F") 
    time.sleep(20)
    driver.click("button#onetrust-accept-btn-handler")
    scroll_page_load(driver)
    listarticles, listToDownload = getArticles(driver, data)
    if(not len(listarticles) == 0): downloadArticles(driver, data, listToDownload)
    return listarticles

"""
Scroll par le bas pour charger les articles
"""
def scroll_page_load(driver):
    for i in range(6):
        container = driver.select("div#search_container_wrapper") 
        container.scroll_to_bottom()
        print(f"{i}eme scroll")
        time.sleep(2)

"""
Télécharge les fichiers qui se télécharge automatiquement dans le dossier "download"
Regarde avant et apres dans le dossier telechargement pour voir les différences 
Pour les nouveaux fichiers, déplace dans le dossier prévu 

params : 
* listToDownload : liste d'article à télécharger
"""
def downloadArticles(driver, data, listToDownload):
    fichiers_avant = set(os.listdir(data["source_folder"]))
    
    for art in listToDownload:
        driver.google_get(art)
        time.sleep(5)
    time.sleep(5)

    fichiers_apres = set(os.listdir(data["source_folder"]))
    nouveaux_fichiers = fichiers_apres - fichiers_avant
        
    for nom_fichier in nouveaux_fichiers :
        chemin_source = os.path.join(data["source_folder"], nom_fichier)
        chemin_destination = os.path.join(data["download_folder"], nom_fichier)
        shutil.move(chemin_source, chemin_destination)
        print("fichier téléchargé et déplacé : ", nom_fichier) 


"""
Récupère les titres des articles de la page
Pour chaque titre 
    si le titre contient tout les mots de la recherxhe
    On récupère des éléments pour reconstruire le lien PDF et on l'ajoute à la liste des articles à télécharger
    Si on ne trouve pas d'article 10 fois d'affilé, on stop et on renvoie les noms d'articles et les liens de téléchargement 
"""
def getArticles(driver, data):
    listarticles = []
    listToDownload = []
    articles = driver.select_all("a[data-test-id^='article_navigate_']")
    compteurSaturation = 0
    for i in articles:
        title = i.select("div.title").text
        title = title.lower()
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
        if(isValid): # on reconstruit le lien du pdf
            doiText = i.select("div.altmetric-embed").get_attribute("data-doi")

            source = i.select("div.source").text
            source = source.split("|")
            source = source[0].split(" ")
            sourcelink = "-".join(source[2:])
            sourcelink = sourcelink[:-1]

            linkDownload = f"https://www.frontiersin.org/journals/{sourcelink}/articles/{doiText}/pdf"

            listarticles.append(title)
            listToDownload.append(linkDownload)

            compteurSaturation = 0

            print("1 article trouvé : ", title)
        else:
            if(compteurSaturation > 10):
                return listarticles, listToDownload 
            compteurSaturation += 1

    return listarticles, listToDownload 
    
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
def getPDF_FRONTIERS(source_folder, download_folder, motRecherche, validRecherche):
    query = "%20".join(motRecherche)
    domain = f"https://www.frontiersin.org/"
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






