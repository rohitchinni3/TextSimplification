package com.example.textsimplification.network;

import org.json.JSONException;
import org.json.JSONObject;

import java.io.IOException;
import java.util.concurrent.TimeUnit;

import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class ApiClient {

    public static final String BASE_URL = "http://10.0.2.2:8000";
    private static final String SIMPLIFY_ENDPOINT = "/api/v1/simplify";
    private static final MediaType JSON = MediaType.get("application/json; charset=utf-8");

    public interface SimplifyCallback {
        void onSuccess(JSONObject result);
        void onError(String errorMessage);
    }

    private final OkHttpClient client;

    public ApiClient() {
        client = new OkHttpClient.Builder()
                .connectTimeout(30, TimeUnit.SECONDS)
                .readTimeout(60, TimeUnit.SECONDS)
                .writeTimeout(30, TimeUnit.SECONDS)
                .build();
    }

    public void simplify(String text, int targetGrade, int maxAttempts, SimplifyCallback callback) {
        JSONObject requestBody = new JSONObject();
        try {
            requestBody.put("text", text);
            requestBody.put("target_fk_grade", targetGrade);
            requestBody.put("max_attempts", maxAttempts);
        } catch (JSONException e) {
            callback.onError("Failed to build request: " + e.getMessage());
            return;
        }

        RequestBody body = RequestBody.create(requestBody.toString(), JSON);
        Request request = new Request.Builder()
                .url(BASE_URL + SIMPLIFY_ENDPOINT)
                .post(body)
                .build();

        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                callback.onError("Could not reach the API. Check that the backend is running at " + BASE_URL);
            }

            @Override
            public void onResponse(Call call, Response response) throws IOException {
                String responseBody = response.body() != null ? response.body().string() : "";
                if (!response.isSuccessful()) {
                    callback.onError("Server error " + response.code() + ": " + responseBody);
                    return;
                }
                try {
                    JSONObject json = new JSONObject(responseBody);
                    callback.onSuccess(json);
                } catch (JSONException e) {
                    callback.onError("Unexpected response from server.");
                }
            }
        });
    }
}
