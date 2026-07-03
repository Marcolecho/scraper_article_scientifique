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
    articles = []
    
    navigateToNextPage(driver, data, 0)
    nbPageMax = getPageMax(driver)
    print("nbPageMax :", nbPageMax)
    for i in range(1, nbPageMax):
        nameArticles = getArticles(driver, data)
        if(len(nameArticles) == 0): return articles
        articles.extend(nameArticles)
        navigateToNextPage(driver, data, i)


"""
Navigue sur la page suivante en modifiant l'url avec le nouveau nombre de page
"""
def navigateToNextPage(driver, data, page):
    domain = data["domain"]
    query = data["query"]
    driver.google_get(f"{domain}/action/doSearch?AllField={query}&pageSize=20&startPage=&target=default&content=articlesChapters&startPage={page}") 
    time.sleep(15)


"""
Récupération du nombre de pages maximum et click pour accepter le cookies
""" 
def getPageMax(driver: Driver):
    time.sleep(30)
    driver.click("button.osano-cm-accept-all.osano-cm-buttons__button.osano-cm-button.osano-cm-button--type_accept")
    nbArticle = (driver.select("span.result__count")).text
    nbArticle = nbArticle.replace(',', '')
    nbArticle = int(nbArticle)
    return math.ceil(nbArticle/20)


"""
Récupère les titres des articles de la page
Pour chaque titre 
    si le titre contient tout les mots de la recherxhe
    On récupère des éléments pour reconstruire le lien PDF et on l'ajoute à la liste des articles à télécharger
    télécharge les articles sélectionné directement
"""
def getArticles(driver, data):
    elements = driver.select_all("div.item__body")
    
    articles_valides = []
    listNameArticles = []

    for i in elements:
        isAccess = i.select("div.doi-access")
        if(not isAccess == None):
            element_article = i.select("a.publication_title.visitable")
            title_text = element_article.text
            title = title_text.lower()
            
            isValid = True
            for listMotsVarValid in data["validRecherche"]:   
                isAtLeastOneValid = False
                for motVarValid in listMotsVarValid:
                    print(motVarValid, title)
                    if motVarValid in title: 

                        isAtLeastOneValid = True
                        break

                if isAtLeastOneValid == False: 
                    isValid = False
                    break
            
            if isValid:
                linkhref = element_article.href
                if linkhref:
                    linkhref = linkhref.replace("/doi/", "/doi/pdfdirect/")
                    linkhref = data["domain"] + linkhref
                    
                    articles_valides.append({
                        "titre": title_text,
                        "url": linkhref
                    })
                    print(f"article valide : ", title_text)
                    listNameArticles.append(title_text)

    print(f"[INFO] {len(articles_valides)} articles valides trouvés sur cette page. Début des téléchargements...")

    if(len(listNameArticles) != 0):
        for art in articles_valides:
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
        
    return listNameArticles

   

"""
Point d'entrée du fichier

Contruit la query (les mots de la recherche à mettre dans l'URL)
Contruit un object contenant toutes les informations importantes
Lance le scraping avec run_browser_scraping
renvoie le nom des pdf trouvés

params : 
* download_folder : Dossier dans lequel poser les pdf
* motRecherche : les mots de la recherche à taper dans les sites
* validRecherche : les mots valides si trouvé
"""
def getPDF_WILEY(download_folder, motRecherche, validRecherche):
    query = "%20".join(motRecherche)
    domain = f"https://onlinelibrary.wiley.com"
    donnees = {
        "motRecherche": motRecherche,
        "domain": domain,
        "download_folder": download_folder,
        "query": query, 
        "validRecherche": validRecherche
    }   
    
    print("Démarrage du processus Botasaurus...")
    listArticles = run_browser_scraping(data=donnees)
    run_browser_scraping.close()
    return listArticles






