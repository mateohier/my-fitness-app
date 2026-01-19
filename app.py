from github import Github

def save_to_github(file_path, content, message="Update data"):
    # Connexion via le token stocké dans les secrets
    g = Github(st.secrets["GITHUB_TOKEN"])
    repo = g.get_repo(st.secrets["REPO_NAME"])
    
    try:
        # Vérifier si le fichier existe déjà pour le mettre à jour
        contents = repo.get_contents(file_path)
        repo.update_file(contents.path, message, content, contents.sha)
    except:
        # Si le fichier n'existe pas, le créer
        repo.create_file(file_path, message, content)

# --- Exemple d'utilisation dans votre bouton "Enregistrer" ---
if st.sidebar.button("💾 Enregistrer"):
    # ... (votre logique de calcul de dataframe) ...
    
    # Conversion du DataFrame en texte CSV
    csv_content = df.to_csv(index=False)
    
    # Envoi vers GitHub
    save_to_github(f"user_data/{user_name}.csv", csv_content, f"Update for {user_name}")
    st.sidebar.success("Données synchronisées sur GitHub !")
