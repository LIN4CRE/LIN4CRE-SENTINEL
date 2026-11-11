package com.lin4cre.sentinel;

import android.content.Context;
import android.content.SharedPreferences;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;

import org.json.JSONObject;

import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/** Stores the companion URL and bearer token encrypted with an Android Keystore AES key. */
final class ConfigStore {
    private static final String PREFS = "sentinel_secure_config";
    private static final String CIPHER_TEXT = "encrypted_config";
    private static final String KEY_ALIAS = "sentinel_companion_config_v1";
    private final Context context;

    ConfigStore(Context context) { this.context = context.getApplicationContext(); }

    void save(String baseUrl, String token) throws Exception {
        JSONObject config = new JSONObject();
        config.put("baseUrl", baseUrl);
        config.put("token", token);
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, getOrCreateKey());
        byte[] encrypted = cipher.doFinal(config.toString().getBytes(StandardCharsets.UTF_8));
        byte[] iv = cipher.getIV();
        byte[] payload = new byte[iv.length + encrypted.length];
        System.arraycopy(iv, 0, payload, 0, iv.length);
        System.arraycopy(encrypted, 0, payload, iv.length, encrypted.length);
        preferences().edit().putString(CIPHER_TEXT, Base64.encodeToString(payload, Base64.NO_WRAP)).apply();
    }

    JSONObject load() throws Exception {
        String encoded = preferences().getString(CIPHER_TEXT, null);
        if (encoded == null) return null;
        byte[] payload = Base64.decode(encoded, Base64.NO_WRAP);
        if (payload.length < 29) throw new IllegalStateException("Stored connection data is invalid");
        byte[] iv = new byte[12];
        byte[] encrypted = new byte[payload.length - iv.length];
        System.arraycopy(payload, 0, iv, 0, iv.length);
        System.arraycopy(payload, iv.length, encrypted, 0, encrypted.length);
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE, getOrCreateKey(), new GCMParameterSpec(128, iv));
        return new JSONObject(new String(cipher.doFinal(encrypted), StandardCharsets.UTF_8));
    }

    void clear() {
        preferences().edit().clear().apply();
        try {
            KeyStore store = KeyStore.getInstance("AndroidKeyStore");
            store.load(null);
            if (store.containsAlias(KEY_ALIAS)) store.deleteEntry(KEY_ALIAS);
        } catch (Exception ignored) { }
    }

    private SharedPreferences preferences() {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    private SecretKey getOrCreateKey() throws Exception {
        KeyStore store = KeyStore.getInstance("AndroidKeyStore");
        store.load(null);
        if (store.containsAlias(KEY_ALIAS)) return (SecretKey) store.getKey(KEY_ALIAS, null);
        KeyGenerator generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
        generator.init(new KeyGenParameterSpec.Builder(KEY_ALIAS,
                KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setRandomizedEncryptionRequired(true)
                .build());
        return generator.generateKey();
    }
}
