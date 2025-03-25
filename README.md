# dans_ma_rue

Objectif: aider la mairie de Paris dans la gestion des données citoyennes récoltées dans l'application Dans Ma Rue

Approche:
1. Télécharger la donnée et la mettre en forme
    1. Feed de l’API, jeu de données complet
    2. Téléchargement du jeu de données complet puis mise à jour quotidienne avec les nouvelles requêtes (~3K) → voir comment filtrer sur la date dès la requête API?
    3. Hosté sur BigQuery
2. Analyser la donnée pour dégager les tendances
    1. Combien de requêtes sont en fait les mêmes problèmes? Comment rendre la donnée plus lisible pour la ville de Paris (+100K requêtes par mois)
        1. Création d’une BDD clusterisée sur python à partir de la table BQ, uploadée sur BQ: clusterisation par Type puis coordonnées par DBSCAN pour regrouper les problèmes qui sont en fait les mêmes (mis à des moments différents, ou à des adresses différentes)
        2. Création de coordonnées par cluster pour la visualisation
            1. Itération sur la création de clusters - 300K cluster sur type puis rayon de 10m → essai sur 20m → 100K clusters
            - En testant les clusters manuellement, il apparaît que le niveau sous-type parait plus approprié, mais celui-ci est probablement trop granulaire / sujet à interprétations et à erreurs, créant des problèmes différents alors que ce sont les mêmes. Etant donné qu’il vaut mieux vaut avoir trop de clusters (faux négatifs) que pas assez, favoriser les sous-types: réduit par ~3 le nombre de requêtes.
                
                
            - Preliminary data exploration: checker cluster 123811 (56K requetes identiques) → à cause de la transitivité de DBSCAN → post-processing requis pour contrôler la distance. DBSCAN utilise la transitivité (A est proche de B, C est poche de B donc A,B et C peuvent être dans le même cluster) et le noise (nombre min de points proches) → il faut donc neutraliser la transitivité en fixant une distance max pour les clusters (ex: 20 mètres) en post-processing. Problème: cela prend 1h.
        3. Comment cette donnée serait utilisée?
            1. Les données sont reçues et envoyées aux services tous les jours → pas pertinent de clusteriser dans le temps pour améliorer les interventions, mais possibilité de vérifier tous les jours quelles requêtes sont en fait les mêmes que d’autres requêtes ouvertes.
                1. Contacter l’équipe Dans Ma rue pour le filtre ouvert / fermé + les dernières données (seulement D-60 actuellement)
            2. Pour tester la logique: Prendre comme filtre tous les problèmes du dernier mois, et matcher le cluster chaque jour pour créer un filtrer problème existant vs nouveau (si données dispos, matcher avec tous les problèmes ouverts)
            3. Output: un tableau avec les nouvelles requêtes et en colonne si elles sont réellement nouvelles ou pas
    2. Quelles sont les problèmes avec la plus grande fréquence et où apparaissent-ils?
        1. Implique de regarder les données dans le temps (requêtes ouvertes et fermées)
        2. Output: Map de clusters et nombre de lignes → density map? Filter in Top 10%?
    3. Visualisation sur Metabase - carte de Paris
        1. Prelim Data Analysis
            1. Too many clusters when setting radius of 10m
3. Prioriser les interventions
    1. Par bureau?
    2. Par quoi?
4. Prédire les problèmes
    1. Selon quoi?
5. Automatiser le processus
    1. Mise à jour hebdomadaire?

- https://opendata.paris.fr/explore/dataset/dans-ma-rue/api/?disjunctive.conseilquartier&disjunctive.intervenant&disjunctive.type&disjunctive.soustype&disjunctive.arrondissement&disjunctive.prefixe&disjunctive.code_postal&refine.conseilquartier=ALIGRE+-+GARE+DE+LYON&refine.anneedecl=2024&dataChart=eyJxdWVyaWVzIjpbeyJjaGFydHMiOlt7InR5cGUiOiJwaWUiLCJmdW5jIjoiQ09VTlQiLCJ5QXhpcyI6ImFycm9uZGlzc2VtZW50Iiwic2NpZW50aWZpY0Rpc3BsYXkiOnRydWUsImNvbG9yIjoicmFuZ2UtY3VzdG9tIiwicG9zaXRpb24iOiJjZW50ZXIifV0sInhBeGlzIjoidHlwZSIsIm1heHBvaW50cyI6MTAwLCJ0aW1lc2NhbGUiOiIiLCJzb3J0Ijoic2VyaWUxLTEiLCJzZXJpZXNCcmVha2Rvd24iOiIiLCJzZXJpZXNCcmVha2Rvd25UaW1lc2NhbGUiOiIiLCJjb25maWciOnsiZGF0YXNldCI6ImRhbnMtbWEtcnVlIiwib3B0aW9ucyI6eyJkaXNqdW5jdGl2ZS5jb25zZWlscXVhcnRpZXIiOnRydWUsImRpc2p1bmN0aXZlLmludGVydmVuYW50Ijp0cnVlLCJkaXNqdW5jdGl2ZS50eXBlIjp0cnVlLCJkaXNqdW5jdGl2ZS5zb3VzdHlwZSI6dHJ1ZSwiZGlzanVuY3RpdmUuYXJyb25kaXNzZW1lbnQiOnRydWUsImRpc2p1bmN0aXZlLnByZWZpeGUiOnRydWUsImRpc2p1bmN0aXZlLmNvZGVfcG9zdGFsIjp0cnVlLCJyZWZpbmUuY29uc2VpbHF1YXJ0aWVyIjoiQUxJR1JFIC0gR0FSRSBERSBMWU9OIiwicmVmaW5lLmFubmVlZGVjbCI6IjIwMjQifX19XSwiZGlzcGxheUxlZ2VuZCI6dHJ1ZSwiYWxpZ25Nb250aCI6dHJ1ZSwidGltZXNjYWxlIjoiIn0%3D&basemap=jawg.dark&location=20,48.8473,2.37511
- https://help.opendatasoft.com/apis/ods-explore-v2/explore_v2.1.html
