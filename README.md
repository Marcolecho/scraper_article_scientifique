# scraper_article_scientifique
Permet de scraper des articles sur différents site : 

* Frontiers 
* MDPI
* PUBSACS
* PUBSRSC
* SCIENCEDIRECT/elsevier
* SPRINGER
* WILEY  


## Condition pour lancer le projet : 

Avoir anaconda

Se mettre dans le projet à l'endroit du fichier scraper.yml.

Faire la commande pour installer l'environnement conda:  

```
conda env create -f scraper.yml
```

Modifier le main.py pour adapter la recherche. (des exemples sont présent dans le fichier)

Pour activer l'environnement conda :
```
conda activate scraper
```

Pour lancer le projet:
```
python.exe main.py
```