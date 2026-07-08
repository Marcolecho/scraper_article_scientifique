import os
import time
import re
from botasaurus.browser import browser, Driver
import math
import glob
import shutil


"""
Boucle principale exécutée par Botasaurus pour la navigation et le scraping
On navigue sur la page principale, on récupère le nombre de page max pour savoir combien de fois boucler maximum
On récupère les articles pertinents tant qu'il y en a dans la page (si un page est cide d'articles pertinent, on stop)
"""
@browser(
    headless=False,
    reuse_driver=True,
    block_images_and_css=False
)
def run_browser_scraping(driver: Driver, data):
    domain = data["domain"]
    motRecherche = data["motRecherche"]
    validRecherche = data["validRecherche"]
    
    listGlobalTitle = []
    listAllPDF = []
    
    query = "%20".join(motRecherche)
    base_url = f"{domain}/search?sort=pubdate&page_no=1&page_count=50&year_from=1996&year_to=2050&q={query}&view=default"
    
    print(f"Navigation vers : {base_url}")
    driver.google_get(base_url)
    time.sleep(5)
    
    nombrePageMax = getPageMax(driver)
    print(f"[INFO] Nombre de pages max détecté : {nombrePageMax}")

    resPDFs, titles = getInfoArticle(driver, validRecherche, domain)
    listAllPDF.extend(resPDFs)
    listGlobalTitle.extend(titles)

    for i in range(2, nombrePageMax + 1):
        if len(titles) == 0: # Si la page précédente n'a rien donné, on stoppe
            print("[INFO] Aucun titre valide sur la page précédente, arrêt précoce.")
            break
            
        print(f"\n--- Collecte des liens : Page {i} / {nombrePageMax} ---")
        next_url = f"{domain}/search?sort=pubdate&page_no={i}&page_count=50&year_from=1996&year_to=2050&q={query}&view=default"
        
        driver.google_get(next_url)
        time.sleep(5)
        
        resPDFs, titles = getInfoArticle(driver, validRecherche, domain)
        listAllPDF.extend(resPDFs)
        listGlobalTitle.extend(titles)

    print(f"\n[INFO] Collecte terminée. {len(listAllPDF)} liens PDF valides trouvés.")
    
    
    downloadArticles(driver, data, listAllPDF)

    return listGlobalTitle

"""
Récupération du nombre de pages maximum
""" 
def getPageMax(driver: Driver):
    div = driver.select("div.content__container.content__container--overflow-initial h1").text
    nombres = re.findall(r'\d+', div)
    return math.ceil(int(nombres[0]) / 50)

"""
Récupère les titres des articles de la page
Pour chaque titre 
    si le titre contient tout les mots de la recherxhe
    On récupère des éléments pour reconstruire le lien PDF et on l'ajoute à la liste des articles à télécharger
    On renvoie les noms d'articles et les liens de téléchargement 
"""
def getInfoArticle(driver: Driver, validRecherche, domain):
    listValidTitle = []
    listPDFOff = []

    titles_elements = driver.select_all("a.title-link")
    pdf_elements = driver.select_all("a.UD_Listings_ArticlePDF")

    for idx, t_el in enumerate(titles_elements):
        title = t_el.text.strip().lower()
        
        # Validation du titre avec tes critères
        isValid = True
        for listMotsVarValid in validRecherche:   
            isAtLeastOneValid = False
            for motVarValid in listMotsVarValid:
                if motVarValid in title: 
                    isAtLeastOneValid = True
                    break

            if not isAtLeastOneValid: 
                isValid = False
                break
        
        if isValid: 
            print("Titre valide trouvé :", t_el.text.strip())
            listValidTitle.append(t_el.text.strip())
            
            if idx < len(pdf_elements):
                href = pdf_elements[idx].get_attribute("href")
                if href:
                    full_pdf_url = domain + href if href.startswith("/") else href
                    listPDFOff.append(full_pdf_url)

    return listPDFOff, listValidTitle  




"""
On boucle sur les articles à télécharger
On télécharge dans le dossier base de l'OS puis on déplace le fichier dans le dossier final prévu à cet effet
Si Chrome n'a pas fini, le fichier finit par .crdownload ou .tmp donc on attend avant qu'il soit fini pour le déplacer
"""
def downloadArticles(driver, data, listToDownload):
    dossier_telechargement = data["source_folder"]
    
    for idx, art in enumerate(listToDownload, 1):
        filename = f"{idx}_MDPI.pdf"
        chemin_final = os.path.join(data["download_folder"], filename)
        
        print(f"[{idx}/{len(listToDownload)}] Lancement du téléchargement pour : {filename}")
        
        driver.google_get(art)
        time.sleep(4) 
        
        file_moved = False
        for _ in range(15): 
            fichiers = glob.glob(os.path.join(dossier_telechargement, "*"))
            if not fichiers:
                time.sleep(1)
                continue
                
            dernier_fichier = max(fichiers, key=os.path.getmtime)
            
            if dernier_fichier.endswith(".crdownload") or dernier_fichier.endswith(".tmp"):
                print("Téléchargement en cours... on attend que Chrome finisse")
                time.sleep(1)
                continue
                
            if os.path.isfile(dernier_fichier):
                try:
                    shutil.move(dernier_fichier, chemin_final)
                    print(f"-> Succès ! '{os.path.basename(dernier_fichier)}' est devenu '{filename}'")
                    file_moved = True
                    break
                except Exception as e:
                    print(f"-> Erreur d'accès au fichier (en cours d'écriture ?) : {e}")
                    time.sleep(1)
        
        if not file_moved:
            print(f"-> [ÉCHEC] Le fichier n'a pas pu être récupéré pour {filename}")
            
        time.sleep(2)

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
def getPDF_MDPI(source_folder, download_folder, motRecherche, validRecherche):
    donnees = {
        "domain": "https://www.mdpi.com",
        "motRecherche": motRecherche,
        "validRecherche": validRecherche,
        "download_folder": download_folder,
        "source_folder": source_folder,
    }
    
    print("Démarrage du processus Botasaurus pour MDPI...")
    listGlobalTitle = run_browser_scraping(data=donnees)
    run_browser_scraping.close()
    return listGlobalTitle