package com.lin4cre.sentinel;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URI;
import java.net.URL;
import java.nio.charset.StandardCharsets;

final class ApiClient {
    private final String baseUrl;
    private final String token;

    ApiClient(String baseUrl, String token) {
        this.baseUrl = baseUrl.replaceAll("/+$", "");
        this.token = token;
    }

    static String validateBaseUrl(String value) throws Exception {
        URI uri = new URI(value.trim());
        if (!"https".equalsIgnoreCase(uri.getScheme()) || uri.getHost() == null
                || uri.getUserInfo() != null || uri.getQuery() != null || uri.getFragment() != null) {
            throw new IllegalArgumentException("Use an HTTPS server URL without a username, password, query or fragment.");
        }
        return uri.toString().replaceAll("/+$", "");
    }

    JSONObject getObject(String path) throws Exception {
        Object result = get(path);
        if (!(result instanceof JSONObject)) throw new IllegalStateException("Unexpected server response");
        return (JSONObject) result;
    }

    JSONArray getArray(String path) throws Exception {
        Object result = get(path);
        if (!(result instanceof JSONArray)) throw new IllegalStateException("Unexpected server response");
        return (JSONArray) result;
    }

    private Object get(String path) throws Exception {
        URL url = new URL(baseUrl + "/api/mobile/v1" + path);
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestMethod("GET");
        connection.setConnectTimeout(8_000);
        connection.setReadTimeout(12_000);
        connection.setInstanceFollowRedirects(false); // never forward the bearer token to a redirect target
        connection.setRequestProperty("Accept", "application/json");
        connection.setRequestProperty("Authorization", "Bearer " + token);
        try {
            int status = connection.getResponseCode();
            InputStream stream = status >= 200 && status < 300 ? connection.getInputStream() : connection.getErrorStream();
            String body = stream == null ? "" : readAll(stream);
            if (status < 200 || status >= 300) {
                if (status == 401) throw new IllegalStateException("The pairing token was rejected. Re-pair the app with SENTINEL.");
                if (status == 503) throw new IllegalStateException("Mobile access is not configured on the SENTINEL server.");
                throw new IllegalStateException("SENTINEL server returned HTTP " + status + ".");
            }
            return body.startsWith("[") ? new JSONArray(body) : new JSONObject(body);
        } finally {
            connection.disconnect();
        }
    }

    private static String readAll(InputStream stream) throws Exception {
        try (InputStream input = stream; ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[4096];
            int count;
            while ((count = input.read(buffer)) != -1) output.write(buffer, 0, count);
            return output.toString(StandardCharsets.UTF_8.name());
        }
    }
}
