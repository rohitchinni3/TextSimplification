package com.example.textsimplification.utils;

public class ValidationUtils {

    public static final int MIN_GRADE = 1;
    public static final int MAX_GRADE = 18;
    public static final int DEFAULT_GRADE = 6;

    private ValidationUtils() {}

    /**
     * Parses the target grade string, returns the integer if valid (1-18),
     * or DEFAULT_GRADE if the string is blank.
     * Throws IllegalArgumentException if the value is present but invalid.
     */
    public static int parseTargetGrade(String input) {
        if (input == null || input.trim().isEmpty()) {
            return DEFAULT_GRADE;
        }
        int value;
        try {
            value = Integer.parseInt(input.trim());
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("Target grade must be a whole number between " + MIN_GRADE + " and " + MAX_GRADE + ".");
        }
        if (value < MIN_GRADE || value > MAX_GRADE) {
            throw new IllegalArgumentException("Target grade must be between " + MIN_GRADE + " and " + MAX_GRADE + ".");
        }
        return value;
    }

    /**
     * Returns true if the input text is non-null and contains at least one non-whitespace character.
     */
    public static boolean isInputValid(String text) {
        return text != null && !text.trim().isEmpty();
    }
}
