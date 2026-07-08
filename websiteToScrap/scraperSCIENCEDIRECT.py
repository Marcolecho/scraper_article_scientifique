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
    headless=True,           # Obligatoire pour voir l'écran et passer les bots
    block_images_and_css=False, 
    reuse_driver=True         
)
def run_browser_scraping(driver: Driver, data):
    articles = []
    accessToRecherch(driver, data)
    pageMax = getPageMax(driver)
    pageMax = int(pageMax)
    for i in range(pageMax):
        listArticles = getArticles(driver, data)
        if(len(listArticles) == 0): # cas ou la page n'a donné aucun résultat, on suppose qu'il n'y a rien d'autre donc on stoppe
            return articles
        articles.extend(listArticles)
        navigateToNextPage(driver)


"""
Valide les cookies
Frappe dans le champ des recherche les mots pertinents et clique sur recherche pour accéder à la recherche
click sur le bouton pour n'avoir que les journaux accessible
"""
def accessToRecherch(driver, data):
    mots_cles = data["motRecherche"]
    driver.google_get("https://www.sciencedirect.com/") 
    time.sleep(10)
    cookie = "#onetrust-accept-btn-handler"
    driver.click(cookie)
    time.sleep(2)
    selecteur_champ = "#qs"
    driver.click(selecteur_champ)
    time.sleep(1)
    for i in mots_cles:
        driver.type(selecteur_champ, i + " ")
        time.sleep(0.5)
    print("beforeSub")

    bouton_recherche = "button[type='submit']"
    driver.click(bouton_recherche)
    time.sleep(5)
    driver.click("#subscribedJournalsToggle")
    time.sleep(10)



"""
Click sur le bouton pour accéder à la page suivante
"""
def navigateToNextPage(driver):
    driver.click("a[data-aa-name='srp-next-page']")
    time.sleep(10)



"""
Récupération du nombre de pages maximum
""" 
def getPageMax(driver: Driver):
    pagination_element = driver.select("#srp-pagination li")
    texte_complet = pagination_element.text
    nombres = re.findall(r'\d+', texte_complet)
    return int(nombres[-1])



"""
Récupère les titres des articles de la page
Pour chaque titre 
    si le titre contient tout les mots de la recherxhe
    On récupère des éléments pour reconstruire le lien PDF et on l'ajoute à la liste des articles à télécharger
    On séléctionne les checkbox associé au articles à télécharger
    On télécharge en .zip les différents fichiers dans le dossier automatique téléchargement
"""
def getArticles(driver, data):
    results = driver.select_all("li.ResultItem.col-xs-24.push-m")
    listTitles = []
    
    for i in results:
        titleArticle = i.select("a.anchor.result-list-title-link.anchor-secondary.u-font-serif.text-s").text
        checkbox = i.select(".checkbox-input")
        
        title = titleArticle.lower()
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
        
        if(isValid): 
            listTitles.append(titleArticle)
            checkbox.click()

        time.sleep(0.1)

    if(len(listTitles) != 0):
        time.sleep(3)
        driver.click("button.button-link.download-all-link-button.active.button-link-primary.button-link-icon-left")
        time.sleep(10)
        driver.click("button.button-link.modal-close-button.move-right.move-top.u-margin-xs.button-link-primary.button-link-icon-only")
        time.sleep(1)

    print("-------")
    return listTitles

"""
Déplace le/les zip dans le dossier_cible et unzip à l'endroit souhaité   

params : 
* dossier_telechargement : dossier de téléchargement base 
* dossier_cible : dossier où poser les pdf
"""
def moveZipToFolder(dossier_telechargement, dossier_cible):
    date_aujourdhui = datetime.now().strftime("%d%b%Y")
    
    prefixe_attendu = "ScienceDirect_articles_"

    for fichier in os.listdir(dossier_telechargement):
        if fichier.startswith(prefixe_attendu) and date_aujourdhui in fichier and fichier.endswith(".zip"):
            chemin_zip_source = os.path.join(dossier_telechargement, fichier)
            chemin_zip_cible = os.path.join(dossier_cible, fichier)

            shutil.move(chemin_zip_source, chemin_zip_cible)
            
            with zipfile.ZipFile(chemin_zip_cible, 'r') as zip_ref:
                zip_ref.extractall(dossier_cible)
                
            os.remove(chemin_zip_cible)


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
def getPDF_SCIENCEDIRECT(download_folder_Web, download_folder, motRecherche, validRecherche):
    domain = "https://www.sciencedirect.com"
    
    donnees = {
        "motRecherche": motRecherche,
        "domain": domain,
        "download_folder": download_folder,
        "validRecherche": validRecherche
    }   
    
    print("Démarrage du processus Botasaurus...")
    listArticles = run_browser_scraping(data=donnees)
    run_browser_scraping.close()
    moveZipToFolder(download_folder_Web, download_folder)
    return listArticles






