## Transcriber – Assistant vocal en ligne

### 🚀 Objectif
Application web qui :
- **écoute ta voix en direct dans le navigateur**,
- **transcrit** ce que tu dis (Whisper),
- **résume** chaque morceau,
- **génère des questions intelligentes** pour approfondir,
- **construit un compte‑rendu structuré en temps réel** (projets, tâches, décisions, etc.).

Tout se fait **en ligne depuis le navigateur**, le serveur ne dépend pas du micro local de la machine serveur.

---

### 🧱 Architecture
- `index.html`  
  - UI moderne : boutons Démarrer/Arrêter, panneaux Transcriptions / Analyses / Compte‑rendu.  
  - Utilise `getUserMedia` + `AudioContext` (16 kHz) pour **capturer le micro côté navigateur**.  
  - Envoie en continu des chunks audio PCM Float32 via **Socket.IO** (`audio_chunk`) au serveur.

- `app.py`  
  - Serveur **Flask + Flask‑SocketIO**.  
  - Événements Socket.IO :
    - `start_recording` : démarre une nouvelle session, réinitialise les données.
    - `audio_chunk` : reçoit les buffers audio du navigateur, lance la transcription/analysis en thread.
    - `stop_recording` : stoppe la session et renvoie le statut final.  
  - Utilise :
    - `transcribe.transcribe_chunk` pour la **transcription Whisper**,
    - `gpt_pipeline.summarise_and_question` pour le **résumé + questions**,
    - `report_generator.generate_live_report` pour le **compte‑rendu JSON structuré**.  
  - Diffuse en temps réel au front :
    - `transcription` : texte brut + timecodes,
    - `analysis` : résumé + liste de questions,
    - `live_report` : objet JSON structuré.

- `transcribe.py`  
  - Charge le modèle Whisper (`small` par défaut).  
  - Reçoit un `np.array` audio + sample rate navigateur.  
  - **Normalise et resample automatiquement en 16 kHz** pour Whisper.  
  - Retourne les `segments` de Whisper (`start`, `end`, `text`).

- `gpt_pipeline.py`  
  - Appelle l’API OpenAI (`gpt-4o`) pour :
    - résumer un chunk de texte en **une phrase**,
    - générer **2 questions** pertinentes.  
  - Retourne une réponse texte multi‑ligne que `app.py` découpe en `summary` + `questions`.

- `report_generator.py`  
  - Appelle l’API OpenAI (`gpt-4o`) pour analyser tout le texte accumulé et produire un **JSON strict** :
    - `projets`, `dates`, `taches`, `personnes`, `chiffres`, `decisions`, `points_cles`, `points`, `nombre de mots`.  
  - `app.py` nettoie la réponse (retire les ```json éventuels) puis parse le JSON et l’envoie au front sous forme d’événement `live_report`.

- `session.json`  
  - Sauvegarde locale de la session (liste de segments : texte, résumé, questions).

- `requirements.txt`  
  - Libs principales :  
    - `git+https://github.com/openai/whisper.git`  
    - `torch`, `torchaudio`  
    - `openai`, `python-dotenv`  
    - `numpy`  
    - `flask`, `flask-socketio`, `eventlet`

---

### ⚙️ Configuration requise
- **Python recommandé : 3.11**  
  (Évite les versions expérimentales comme 3.14 pour Whisper & co.)
- Variable d’environnement :
  - `OPENAI_API_KEY` : clé OpenAI avec accès aux modèles `gpt-4o`.

Sur ton poste local :
```bash
export OPENAI_API_KEY="ta_cle"
```

Sur un hébergeur (Render, Railway, etc.) :
- Ajoute `OPENAI_API_KEY` dans les **variables d’environnement** du service.

---

### ▶️ Lancer en local (optionnel)
Dans le dossier du projet :

```bash
pip install -r requirements.txt
export OPENAI_API_KEY="ta_cle"
python app.py
```

Puis ouvre dans ton navigateur :
- `http://localhost:5000`

La page te demandera l’accès au **micro**.  
Quand tu cliques sur **Démarrer** :
- le front envoie tes chunks audio au serveur,
- le serveur transcrit, résume, pose des questions,
- le compte‑rendu se met à jour en direct.

---

### 🌐 Mise en ligne (déploiement)
Plusieurs options :

#### 1. Hébergement type Render / Railway
1. Pousser ce repo sur GitHub (`hvmedx/Transcriber`).  
2. Créer un nouveau service web sur la plateforme choisie en pointant sur ce repo.  
3. Configurer :
   - **Build command** :  
     `pip install -r requirements.txt`
   - **Start command** :  
     `python app.py`
   - **Env** : `OPENAI_API_KEY`.
4. La plateforme expose ensuite une URL publique (HTTPS).

#### 2. Docker (optionnel)
Exemple de `Dockerfile` minimal :

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV OPENAI_API_KEY=changeme
EXPOSE 5000
CMD ["python", "app.py"]
```

Build & run :
```bash
docker build -t transcriber .
docker run -p 5000:5000 -e OPENAI_API_KEY="ta_cle" transcriber
```

---

### 🧪 Fonctionnalités actuelles
- **Transcription en direct** (français, via Whisper).
- **Résumés automatiques** par segment.
- **Questions de relance** pour approfondir ce que tu dis au fur et à mesure.
- **Compte‑rendu structuré en temps réel** (projets, tâches, décisions, etc.).
- **Interface web moderne** avec trois panneaux :
  - Transcriptions,
  - Analyses & Questions,
  - Compte Rendu en Temps Réel.

---

### ✅ Roadmap possible
- Support multilingue (détection automatique de la langue).
- Export du compte‑rendu (PDF / Markdown / Notion).
- Gestion multi‑utilisateurs / authentification.
- Passage de l’audio en binaire (WebSocket + ArrayBuffer) pour optimiser la bande passante.


