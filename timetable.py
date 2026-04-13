import json
from ortools.sat.python import cp_model

def load_data():
    with open('rooms.json', 'r', encoding='utf-8') as f:
        rooms_data = json.load(f)
    with open('subjects.json', 'r', encoding='utf-8') as f:
        subjects_data = json.load(f)
    return rooms_data, subjects_data

rooms_json, subjects_json = load_data()

salles = [r['num'] for r in rooms_json['Informatique']]

jours = range(1, 7) 
periodes = range(1, 6)

poids_periodes = {1: 50, 2: 40, 3: 30, 4: 20, 5: 10} 

cours_par_niveau = {}
tous_les_enseignants = set()
liste_cours = []

for niv, semestres in subjects_json['niveau'].items():
    if 's1' in semestres:
        cours_par_niveau[niv] = []
        for s in semestres['s1']['subjects']:
            lecturers = s.get('Course Lecturer', [])
            if lecturers and len(lecturers) > 0 and lecturers[0] != "":
                prof = lecturers[0]
            else:
                prof = "Inconnu"
            
            tous_les_enseignants.add(prof)
            info_cours = {
                'code': s.get('code', 'N/A'),
                'nom': s.get('name', 'N/A'),
                'prof': prof,
                'niveau': niv
            }
            cours_par_niveau[niv].append(info_cours)
            liste_cours.append(info_cours)

model = cp_model.CpModel()
X = {}

for c in liste_cours:
    for r in salles:
        for d in jours:
            for p in periodes:
                X[(c['code'], r, d, p)] = model.NewBoolVar(f"x_{c['code']}_{r}_{d}_{p}")

for niv in cours_par_niveau:
    for d in jours:
        for p in periodes:
            model.Add(sum(X[(c['code'], r, d, p)] 
                          for c in cours_par_niveau[niv] 
                          for r in salles) <= 1)

for c in liste_cours:
    model.Add(sum(X[(c['code'], r, d, p)] 
                  for r in salles 
                  for d in jours 
                  for p in periodes) == 1)

enseignants_list = list(tous_les_enseignants)
for prof in enseignants_list:
    for d in jours:
        for p in periodes:
            codes_du_prof = [c['code'] for c in liste_cours if c['prof'] == prof]
            if codes_du_prof:
                model.Add(sum(X[(code, r, d, p)] for code in codes_du_prof for r in salles) <= 1)

for r in salles:
    for d in jours:
        for p in periodes:
            model.Add(sum(X[(c['code'], r, d, p)] for c in liste_cours) <= 1)

objective_terms = []
for (code, r, d, p), var in X.items():
    poids = poids_periodes[p]
    objective_terms.append(var * poids)

model.Maximize(sum(objective_terms))

solver = cp_model.CpSolver()
status = solver.Solve(model)

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print(f"Solution trouvée ! (Statut : {solver.StatusName(status)})\n")
    results = []
    for (code, r, d, p), var in X.items():
        if solver.Value(var) == 1:
            c_info = next(item for item in liste_cours if item['code'] == code)
            results.append((d, p, c_info['niveau'], code, r, c_info['prof']))
    
    results.sort() 
    
    nom_jours = {1:"Lundi", 2:"Mardi", 3:"Mercredi", 4:"Jeudi", 5:"Vendredi", 6:"Samedi"}
    for res in results:
        print(f"{nom_jours[res[0]]} | Période {res[1]} | Niveau {res[2]} | {res[3]} | Salle: {res[4]} | Prof: {res[5]}")
else:
    print("Aucune solution trouvée respectant toutes les contraintes.")