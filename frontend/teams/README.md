# How to side-load Ops IQ into Microsoft Teams

1. **Create the App Package (ZIP file)**:
   A Microsoft Teams App Package is just a `.zip` file containing 3 things at the root level:
   - `manifest.json` (this file)
   - `color.png` (a 192x192 colored icon)
   - `outline.png` (a 32x32 transparent outline icon)

   To build this package:
   - Edit the `manifest.json` and replace `contentUrl`, `validDomains` and `${VITE_AZURE_CLIENT_ID}` with your real deployment URL and Azure details.
   - Add your own `color.png` and `outline.png` images inside this `teams/` directory.
   - Select the 3 files and compress them into `OpsIQ_TeamsApp.zip`.

2. **Run a secure tunnel (Local Dev Only)**:
   Teams requires `https://` URLs, so to point Teams to your local dev environment (`http://localhost:5173`), you must run a tunnel like Ngrok or Dev Tunnels.
   ```bash
   ngrok http 5173
   ```
   Paste the resulting `https://` string into the `contentUrl` property in the `manifest.json`.

3. **Side-load the App in Teams**:
   - Open Microsoft Teams.
   - Go to "Apps" -> "Manage your apps" -> "Upload an app" -> "Upload a custom app".
   - Select your newly created `OpsIQ_TeamsApp.zip`.
   - The app will be added as a personal tab. Click "Add".

4. **Testing Authentication**:
   Inside Teams, when you navigate to the tab, the `isTeamsContext` flag in `AuthContext.tsx` will trigger `microsoftTeams.authentication.getAuthToken()`. This will securely grab the SSO token representing you, allowing the OpsIQ backend to route your requests.
