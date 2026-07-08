# scraper_article_scientifique
## Sur windows

Permet de scraper des articles sur différents site : 

* Frontiers 
* MDPI
* PUBSACS
* PUBSRSC
* SCIENCEDIRECT/elsevier
* SPRINGER
* WILEY  

<br><br>

## Condition pour lancer le projet : 

* Avoir anaconda
* Avoir google chrome

<br><br>

## Mise en place

Se mettre dans le projet à l'endroit du fichier environment.yml  

Faire la commande pour installer l'environnement conda:  

```
(pour linux, faire "iconv -f UTF-16 -t UTF-8 environment.yml -o environment_clean.yml" et retirer les dépendances unique à Windows qui sont donnés en essayant de créer l'environement)
conda env create -f environment.yml -n scraper (environment_clean.yml pour linux)
```

Modifier le main.py pour adapter la recherche. (des exemples sont présent dans le fichier)

Pour activer l'environnement conda :
```
conda activate scraper
```

## Pour lancer le projet:
```
python.exe main.py
```


## lien schéma
https://canva.link/crcfasqalqnfjql 
