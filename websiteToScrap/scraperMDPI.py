import os
import time
import re
from playwright.sync_api import sync_playwright

"""
Crée le contexte et navigue vers la page cible en fonction du numéro de page et des mots de recherche 
"""
def navigateToWebPage(p, numberPage, motRecherche, domain):
    query = "%20".join(motRecherche)
    base_url = f"{domain}/search?sort=pubdate&page_no={numberPage}&page_count=50&year_from=1996&year_to=2050&q={query}&view=default"
    
    browser = p.chromium.launch(headless=False) # pour afficher la page sinon ça fonctionne pas 
    context = browser.new_context(
        viewport={'width': 1280, 'height': 800},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page = context.new_page()
    
    print(f"Navigation vers : {base_url}")
    page.goto(base_url, wait_until="networkidle")
    
    print("Attente du chargement complet...")
    time.sleep(10)
    return browser, page


"""
On récupère tous les liens de pdf valide (qui contiennent un href)

On récupère tous les titres de la page et on regarde s'il contient tous les mots de validRecherche
Si c'est le cas on l'ajoute à la liste de articles valide
si l'article à un lien pdf valide, alors on l'ajoute à la liste des fichiers à télécharger

params : 
* page : page web à analyser
* validRecherche : mots à valider dans les titres des articles
* domain : nom de domaine 
"""
def getInfoArticle(page, validRecherche, domain):
    listValidTitle = []

    # PDF possibles
    dataPDF = page.locator("a.UD_Listings_ArticlePDF")
    liens_pdf = dataPDF.evaluate_all("elements => elements.map(el => el.getAttribute('href'))")
    listPDFPossible = [domain + lien for lien in liens_pdf if lien]

    # Titres
    # Si les mots de la recherche sont tous dans le titre, alors, on garde ce pdf
    listTitleResult = []
    dataTitle = page.locator("a.title-link")
    titles = dataTitle.evaluate_all("elements => elements.map(el => el.textContent.trim())")
    for title in titles:
        title = title.lower()
        isValid = True
        for listMotsVarValid in validRecherche:   
            isAtLeastOneValid = False
            for motVarValid in listMotsVarValid:
                if motVarValid in title: 
                    isAtLeastOneValid = True
                    break

            if isAtLeastOneValid == False: 
                isValid = False
                break
        listTitleResult.append({"isValid": isValid})
        if(isValid): 
            print("title :", title)
            listValidTitle.append(title)

    """
    # Abstracts
    # Si dans au moins une phrase de l'abstract on retrouve tout les mots de la recherche, alors, on garde ce pdf
    listAbstractsResult = []
    dataAbstract = page.locator("div.abstract-full")
    abstracts = dataAbstract.evaluate_all("elements => elements.map(el => el.textContent.trim())")
    for abstract in abstracts:
        abstract_lower = abstract.lower()
        sentences = abstract_lower.split(".")
        isCurrentAbstractValid = False
        
        for sentence in sentences:
            isAllWordInSentence = True
            for motRech in motRecherche:   
                if motRech not in sentence: 
                    isAllWordInSentence = False
                    break
            if isAllWordInSentence:
                isCurrentAbstractValid = True
                break 
                
        listAbstractsResult.append({"isValid": isCurrentAbstractValid})
    """
    
    # On récupère les index des pdf valides
    indexPDFToRecup = []
    for index, i in enumerate(listTitleResult):
        if i["isValid"]: indexPDFToRecup.append(index)
    #for index, i in enumerate(listAbstractsResult):
        #if i["isValid"]: indexPDFToRecup.append(index)
    indexPDFToRecup = list(set(indexPDFToRecup))

    listPDFOff = []
    for index, i in enumerate(listPDFPossible):
        if(index in indexPDFToRecup):
            listPDFOff.append(i) 
    return listPDFOff, listValidTitle  




"""
Si il y a au moins un fichier à téléchargé
Pour chaque pdf, on lance le téléchargement que l'on dépose dans le download_folder

params : 
* listAllPDF : liste des pdf à télécharger
* download_folder : Dossier dans lequel poser les pdf
* p : navigateur
"""
def downloadPDF(listAllPDF, download_folder, p): 
        if listAllPDF:
            print("\n=== DÉBUT DU TÉLÉCHARGEMENT DES PDF ===")
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            page = context.new_page()

            # On ouvre une page blanche neutre pour ne pas perturber les requêtes
            page.goto("about:blank")

            for i, pdf_url in enumerate(listAllPDF, 1):
                filename = f"{i}_MDPI.pdf"
                filepath = os.path.join(download_folder, filename)
            
                print(f"[{i}/{len(listAllPDF)}] Téléchargement de : {filename}...")
                
                with page.expect_download(timeout=60000) as download_info:
                    page.evaluate(f"""
                        () => {{
                            const a = document.createElement('a');
                            a.href = '{pdf_url}';
                            document.body.appendChild(a);
                            a.click();
                            document.body.removeChild(a);
                        }}
                    """)
                
                download = download_info.value
                download.save_as(filepath)
                print("-> Sauvegardé avec succès.")
                
                time.sleep(3)

"""
Récupération du nombre de pages maximum
""" 
def getPageMax(page):
    container = page.locator(".listing-select-options")
    target_div = container.locator("div:has-text('Displaying article')")
    div_texte = target_div.first.inner_text()
    return int((re.findall(r'\d+', div_texte))[3])


"""
Point d'entrée du fichier

Accède à la page web et récupère le nombre de page max pour savoir combien de fois boucler et changer de page
récupère les articles pertinents. Si il n'y a aucun article pertinent dans la page, on stop
On télécharge les pdfs récupéré et on renvoie les noms d'articles 

params : 
* download_folder : Dossier dans lequel poser les pdf
* motRecherche : les mots de la recherche à taper dans les sites
* validRecherche : les mots valides si trouvé
"""
def getPDF_MDPI(download_folder, motRecherche, validRecherche):
    with sync_playwright() as p:
        domain = "https://www.mdpi.com"
        listGlobalTitle = []
        browser, page = navigateToWebPage(p, 1, motRecherche, domain)

        nombrePageMax = getPageMax(page)

        listAllPDF, listGlobalTitle = getInfoArticle(page, validRecherche, domain)
        browser.close() 

        for i in range(2, nombrePageMax + 1):
            print(f"\n--- Collecte des liens : Page {i} / {nombrePageMax} ---")
            browser, page = navigateToWebPage(p, i, motRecherche, domain)
            resPDFs, titles = getInfoArticle(page, validRecherche, domain)
            if(len(titles) == 0):
                browser.close()
                break
            listAllPDF.extend(resPDFs)
            listGlobalTitle.extend(titles)
            browser.close()

        print(f"\n[INFO] Phase de collecte terminée. {len(listAllPDF)} liens PDF valides trouvés.")
                    
        downloadPDF(listAllPDF, download_folder, p)

        browser.close()

    return listGlobalTitle