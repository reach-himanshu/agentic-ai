# MS Teams Integration Plan

## Goal Description
The objective is to embed the existing React/Vite Ops IQ UI into Microsoft Teams as a Tab Application, without breaking the current Web or Tauri desktop deployments. 

Because Teams Tabs run inside sandboxed `iframes`, standard MSAL authentication methods (like `loginPopup` or `loginRedirect`) will be blocked by the browser. To solve this, we must conditionally integrate the Microsoft Teams JS SDK to handle authentication natively when the app detects it is running inside the Teams client.

## Proposed Architecture & Changes

### 1. Teams SDK Integration
We need to add the `@microsoft/teams-js` dependency to the frontend. This library allows the web app to communicate with the Teams desktop/web host.

#### [MODIFY] frontend/package.json
- Add `"@microsoft/teams-js": "^2.x.x"` to dependencies.
- Add a script to package the Teams manifest into a deployable `.zip` file.

### 2. Contextual Authentication
We will modify the AuthContext to detect the environment context (Teams vs. Web vs. Tauri).

#### [MODIFY] frontend/src/context/AuthContext.tsx
- Initialize the Teams SDK (`app.initialize()`) on load.
- If `app.isInitialized()` is true, intercept the `signIn` function.
- Instead of calling MSAL's `instance.loginPopup()` (which fails in iframes), we will use Teams SSO via `app.authentication.getAuthToken()` or `app.authentication.authenticate()` to securely acquire the Entra ID token using the Teams native popup mechanism.
- For standard web browsers and Tauri apps, the existing MSAL flow will remain completely unchanged.

### 3. Teams App Manifest
Teams requires a manifest package to define the Tab app.

#### [NEW] `frontend/teams/manifest.json`
- Create a Teams manifest configuration defining a "Static Tab" that points to the hosted URL of the frontend.
- Add required `color.png` and `outline.png` icons.
- Define `webApplicationInfo` to link the Teams app to the existing Azure Application Client ID used by MSAL.

### 4. Hosting and Development
- **Local Dev**: To test inside Teams, the Vite dev server (`localhost:5173`) must be exposed over HTTPS using a tunneling service like `ngrok` or Microsoft Dev Tunnels, because Teams will not load `http://localhost`.
- **Production**: The frontend just needs to be hosted on any HTTPS edge (Azure Static Web Apps, Vercel, etc.) and the Teams app simply embeds that URL.

## Verification Plan
1. **Regression Testing**: Verify that running `npm run dev` and accessing via standard browser still works using `loginPopup`. Verify Tauri desktop build still works.
2. **Teams Local Test**: Sideload the generated `manifest.zip` into the local Teams client pointing an ngrok tunnel to `localhost:5173`.
3. **Auth Test**: Ensure clicking "Sign In" inside the Teams tab successfully acquires the Entra ID token and connects to the backend IIS server.
