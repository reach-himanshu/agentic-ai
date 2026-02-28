import type { Configuration, PopupRequest } from "@azure/msal-browser";

/**
 * Configuration object to be passed to MSAL instance on creation. 
 * For a full list of MSAL.js configuration parameters, visit:
 * https://github.com/AzureAD/microsoft-authentication-library-for-js/blob/dev/lib/msal-browser/docs/configuration.md 
 */
export const msalConfig: Configuration = {
    auth: {
        clientId: import.meta.env.VITE_AZURE_CLIENT_ID || "ENTER_CLIENT_ID_HERE",
        authority: `https://login.microsoftonline.com/${import.meta.env.VITE_AZURE_TENANT_ID || "common"}`,
        redirectUri: window.location.origin,
        postLogoutRedirectUri: window.location.origin,
    },
    cache: {
        cacheLocation: "sessionStorage",
        storeAuthStateInCookie: true,
    }
};

export const loginRequest: PopupRequest = {
    scopes: ["User.Read", import.meta.env.VITE_AZURE_BACKEND_SCOPE || "ENTER_BACKEND_SCOPE_URI_HERE"]
};

export const tokenRequest = {
    scopes: [import.meta.env.VITE_AZURE_BACKEND_SCOPE || "ENTER_BACKEND_SCOPE_URI_HERE"]
};
