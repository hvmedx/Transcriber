import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_live_report(text):
    """
    Génère un compte rendu structuré détectant projets, dates, tâches, etc.
    """
    if not text or len(text.strip()) < 15:
        return None
    
    prompt = f"""
    Analyse ce texte et extrais les informations clés sous forme de compte rendu structuré :
    
    Texte : "{text}"
    
    Retourne UNIQUEMENT un JSON avec cette structure (sans texte avant ou après) :
    {{
        "projets": ["liste des projets mentionnés"],
        "dates": ["liste des dates/échéances"],
        "taches": ["liste des actions/tâches à faire"],
        "personnes": ["liste des personnes mentionnées"],
        "chiffres": ["liste des chiffres/montants importants"],
        "decisions": ["liste des décisions prises"],
        "points_cles": ["liste des points importants"],
        "points": ["liste des points à clarifier"],
        "nombre de mots": ["compte le nombre de mots"]
    }}
    
    Si une catégorie est vide, mets un tableau vide [].
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        return f'{{"error": "Erreur API: {str(e)}"}}'
