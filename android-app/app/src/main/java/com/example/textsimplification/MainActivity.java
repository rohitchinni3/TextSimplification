package com.example.textsimplification;

import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.res.ColorStateList;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.ContextCompat;

import com.example.textsimplification.databinding.ActivityMainBinding;
import com.example.textsimplification.network.ApiClient;
import com.example.textsimplification.utils.ValidationUtils;

import org.json.JSONObject;

import java.util.Locale;

public class MainActivity extends AppCompatActivity {

    private ActivityMainBinding binding;
    private ApiClient apiClient;
    private final Handler mainHandler = new Handler(Looper.getMainLooper());

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityMainBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());
        apiClient = new ApiClient();
        binding.progressBar.setIndeterminateTintList(
                ColorStateList.valueOf(ContextCompat.getColor(this, R.color.blue_primary)));
        setupListeners();
    }

    private void setupListeners() {
        binding.btnSimplify.setOnClickListener(v -> onSimplifyClicked());
        binding.btnCopy.setOnClickListener(v -> onCopyClicked());
        binding.btnClear.setOnClickListener(v -> onClearClicked());
    }

    private void onSimplifyClicked() {
        String inputText = binding.etInputText.getText() != null
                ? binding.etInputText.getText().toString() : "";

        if (!ValidationUtils.isInputValid(inputText)) {
            showError(getString(R.string.error_empty_input));
            return;
        }

        String gradeStr = binding.etTargetGrade.getText() != null
                ? binding.etTargetGrade.getText().toString() : "";
        int targetGrade;
        try {
            targetGrade = ValidationUtils.parseTargetGrade(gradeStr);
        } catch (IllegalArgumentException e) {
            showError(e.getMessage());
            return;
        }

        showLoading(true);
        hideResults();
        showStatus(getString(R.string.loading), R.color.blue_primary);

        apiClient.simplify(inputText.trim(), targetGrade, 5, new ApiClient.SimplifyCallback() {
            @Override
            public void onSuccess(JSONObject result) {
                mainHandler.post(() -> handleSuccess(result));
            }

            @Override
            public void onError(String errorMessage) {
                mainHandler.post(() -> {
                    showLoading(false);
                    showError(errorMessage);
                });
            }
        });
    }

    private void handleSuccess(JSONObject result) {
        showLoading(false);
        try {
            String simplifiedText = result.getString("simplified_text");
            double originalFk = result.getDouble("original_fk_grade");
            double finalFk = result.getDouble("final_fk_grade");
            double targetFk = result.getDouble("target_fk_grade");
            boolean targetMet = result.getBoolean("target_met");
            int attempts = result.getInt("attempts");
            String providerMode = result.getString("provider_mode");

            binding.tvSimplifiedText.setText(simplifiedText);
            binding.tvOriginalFk.setText(String.format(Locale.US, "%.1f", originalFk));
            binding.tvFinalFk.setText(String.format(Locale.US, "%.1f", finalFk));
            binding.tvTargetFk.setText(String.format(Locale.US, "%.1f", targetFk));
            binding.tvTargetMet.setText(targetMet ? getString(R.string.yes) : getString(R.string.no));
            binding.tvAttempts.setText(String.valueOf(attempts));
            binding.tvProvider.setText(providerMode);

            int metColor = targetMet
                    ? ContextCompat.getColor(this, R.color.success_green)
                    : ContextCompat.getColor(this, R.color.error);
            binding.tvTargetMet.setTextColor(metColor);

            clearStatus();
            showResults();
        } catch (Exception e) {
            showError(getString(R.string.error_malformed_response));
        }
    }

    private void onCopyClicked() {
        String text = binding.tvSimplifiedText.getText().toString();
        if (!text.isEmpty()) {
            ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
            ClipData clip = ClipData.newPlainText("Simplified Text", text);
            clipboard.setPrimaryClip(clip);
            Toast.makeText(this, getString(R.string.copied_to_clipboard), Toast.LENGTH_SHORT).show();
        }
    }

    private void onClearClicked() {
        if (binding.etInputText.getText() != null) {
            binding.etInputText.getText().clear();
        }
        if (binding.etTargetGrade.getText() != null) {
            binding.etTargetGrade.getText().clear();
            binding.etTargetGrade.setText(String.valueOf(ValidationUtils.DEFAULT_GRADE));
        }
        clearStatus();
        hideResults();
    }

    private void showLoading(boolean show) {
        binding.progressBar.setVisibility(show ? View.VISIBLE : View.GONE);
        binding.btnSimplify.setEnabled(!show);
    }

    private void showResults() {
        binding.cardResults.setVisibility(View.VISIBLE);
    }

    private void hideResults() {
        binding.cardResults.setVisibility(View.GONE);
    }

    private void showError(String message) {
        showStatus(message, R.color.error);
    }

    private void showStatus(String message, int colorResId) {
        binding.tvStatus.setVisibility(View.VISIBLE);
        binding.tvStatus.setText(message);
        binding.tvStatus.setTextColor(ContextCompat.getColor(this, colorResId));
    }

    private void clearStatus() {
        binding.tvStatus.setVisibility(View.GONE);
        binding.tvStatus.setText("");
    }
}
