#!/usr/bin/env node

import http from "node:http";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import { pathToFileURL } from "node:url";

function expandHome(path) {
    if (typeof path !== "string" || !path.startsWith("~/")) {
        return path;
    }
    return join(homedir(), path.slice(2));
}

const PI_MONO_DIR = expandHome(process.env.PI_MONO_DIR || "~/code/pi-mono");
const AUTH_PATH = join(PI_MONO_DIR, "auth.json");
const CODEX_AUTH_FALLBACK_PATH = join(homedir(), ".codex", "auth.json");
const HOST = process.env.PI_AI_SERVER_HOST || "127.0.0.1";
const PORT = Number(process.env.PI_AI_SERVER_PORT || 3456);
const EXPIRY_SKEW_MS = 60_000;

const { completeSimple } = await import(
    pathToFileURL(join(PI_MONO_DIR, "packages/ai/dist/stream.js")).href
);
const { refreshOpenAICodexToken } = await import(
    pathToFileURL(join(PI_MONO_DIR, "packages/ai/dist/utils/oauth/openai-codex.js")).href
);
const { refreshGoogleCloudToken } = await import(
    pathToFileURL(join(PI_MONO_DIR, "packages/ai/dist/utils/oauth/google-gemini-cli.js")).href
);

function loadJson(path) {
    if (!existsSync(path)) {
        return null;
    }
    try {
        return JSON.parse(readFileSync(path, "utf8"));
    } catch {
        return null;
    }
}

function saveJson(path, value) {
    mkdirSync(dirname(path), { recursive: true });
    writeFileSync(path, JSON.stringify(value, null, 2), "utf8");
}

function decodeJwtPayload(token) {
    try {
        const parts = token.split(".");
        if (parts.length !== 3) {
            return null;
        }
        const payload = parts[1].replace(/-/g, "+").replace(/_/g, "/");
        const padded = payload + "=".repeat((4 - (payload.length % 4)) % 4);
        return JSON.parse(Buffer.from(padded, "base64").toString("utf8"));
    } catch {
        return null;
    }
}

function readPiAuth() {
    return loadJson(AUTH_PATH) || {};
}

function writePiAuth(auth) {
    saveJson(AUTH_PATH, auth);
}

function readCodexCliAuth() {
    const raw = loadJson(CODEX_AUTH_FALLBACK_PATH);
    const tokens = raw?.tokens;
    if (!tokens?.access_token || !tokens?.refresh_token) {
        return null;
    }

    const payload = decodeJwtPayload(tokens.access_token);
    const accountId =
        tokens.account_id ||
        payload?.["https://api.openai.com/auth"]?.chatgpt_account_id ||
        null;

    return {
        type: "oauth",
        access: tokens.access_token,
        refresh: tokens.refresh_token,
        expires: typeof payload?.exp === "number" ? payload.exp * 1000 : 0,
        accountId,
    };
}

async function resolveOpenAICodexApiKey() {
    const auth = readPiAuth();
    let creds = auth["openai-codex"];

    if ((!creds?.access || !creds?.refresh) && existsSync(CODEX_AUTH_FALLBACK_PATH)) {
        const fallback = readCodexCliAuth();
        if (fallback) {
            auth["openai-codex"] = fallback;
            writePiAuth(auth);
            creds = fallback;
        }
    }

    if (!creds?.access && !creds?.refresh) {
        return null;
    }

    if (creds?.refresh && Number(creds.expires || 0) <= Date.now() + EXPIRY_SKEW_MS) {
        try {
            const refreshed = await refreshOpenAICodexToken(creds.refresh);
            auth["openai-codex"] = { type: "oauth", ...refreshed };
            writePiAuth(auth);
            creds = auth["openai-codex"];
        } catch (error) {
            if (!creds.access) {
                throw error;
            }
            console.error(
                "[pi-ai-server-compat] openai-codex refresh failed, using cached access token:",
                error instanceof Error ? error.message : String(error),
            );
        }
    }

    return typeof creds?.access === "string" && creds.access ? creds.access : null;
}

async function resolveGeminiCliApiKey() {
    const auth = readPiAuth();
    let creds = auth["google-gemini-cli"];

    if (!creds?.projectId) {
        return null;
    }

    if (creds?.refresh && Number(creds.expires || 0) <= Date.now() + EXPIRY_SKEW_MS) {
        const refreshed = await refreshGoogleCloudToken(creds.refresh, creds.projectId);
        auth["google-gemini-cli"] = { type: "oauth", ...creds, ...refreshed };
        writePiAuth(auth);
        creds = auth["google-gemini-cli"];
    }

    if (typeof creds?.access !== "string" || !creds.access) {
        return null;
    }

    return JSON.stringify({
        token: creds.access,
        projectId: creds.projectId,
    });
}

async function resolveOAuthApiKey(providerId) {
    switch (providerId) {
        case "openai-codex":
            return resolveOpenAICodexApiKey();
        case "google-gemini-cli":
            return resolveGeminiCliApiKey();
        default:
            return null;
    }
}

function normalizeModel(model) {
    const normalized = { ...(model || {}) };
    if (
        normalized.provider === "openai-codex" ||
        normalized.api === "openai-codex-responses"
    ) {
        normalized.baseUrl = "https://chatgpt.com/backend-api";
    }
    return normalized;
}

function normalizeOptions(model, options) {
    const normalized = { ...(options || {}) };
    if (
        typeof model?.id === "string" &&
        model.id.startsWith("gpt-5.4") &&
        normalized.reasoning === "minimal"
    ) {
        normalized.reasoning = "low";
    }
    return normalized;
}

function normalizeContext(model, context) {
    const normalized = { ...(context || {}) };
    if (!Array.isArray(normalized.messages)) {
        normalized.messages = [];
    }
    if (
        (model?.provider === "openai-codex" || model?.api === "openai-codex-responses") &&
        (!normalized.systemPrompt || !String(normalized.systemPrompt).trim())
    ) {
        normalized.systemPrompt = "You are a helpful assistant.";
    }
    return normalized;
}

function sendJson(res, statusCode, payload) {
    res.writeHead(statusCode, { "Content-Type": "application/json" });
    res.end(JSON.stringify(payload));
}

function readJsonBody(req) {
    return new Promise((resolve, reject) => {
        let body = "";
        req.on("data", (chunk) => {
            body += chunk;
        });
        req.on("end", () => {
            if (!body) {
                resolve({});
                return;
            }
            try {
                resolve(JSON.parse(body));
            } catch (error) {
                reject(error);
            }
        });
        req.on("error", reject);
    });
}

const server = http.createServer(async (req, res) => {
    try {
        if (req.method === "GET" && req.url === "/health") {
            sendJson(res, 200, { ok: true });
            return;
        }

        if (req.method === "POST" && req.url === "/auth/token") {
            const body = await readJsonBody(req);
            const providerId = body?.providerId;
            const apiKey = await resolveOAuthApiKey(providerId);
            sendJson(res, 200, { apiKey });
            return;
        }

        if (req.method === "POST" && req.url === "/complete") {
            const body = await readJsonBody(req);
            const model = normalizeModel(body?.model);
            const context = normalizeContext(model, body?.context);
            const options = normalizeOptions(model, body?.options);

            if (!model?.id || !model?.api || !model?.provider) {
                sendJson(res, 400, { error: "Missing model.id/api/provider" });
                return;
            }

            const response = await completeSimple(model, context, options);
            if (response?.stopReason === "error") {
                sendJson(res, 500, { error: response.errorMessage || "LLM request failed" });
                return;
            }

            sendJson(res, 200, response);
            return;
        }

        sendJson(res, 404, { error: "Not found" });
    } catch (error) {
        sendJson(res, 500, {
            error: error instanceof Error ? error.message : String(error),
        });
    }
});

server.listen(PORT, HOST, () => {
    console.error(`[pi-ai-server-compat] listening on http://${HOST}:${PORT}`);
});
