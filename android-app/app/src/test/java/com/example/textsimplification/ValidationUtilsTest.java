package com.example.textsimplification;

import com.example.textsimplification.utils.ValidationUtils;

import org.junit.Test;

import static org.junit.Assert.*;

public class ValidationUtilsTest {

    @Test
    public void parseTargetGrade_nullReturnsDefault() {
        assertEquals(ValidationUtils.DEFAULT_GRADE, ValidationUtils.parseTargetGrade(null));
    }

    @Test
    public void parseTargetGrade_emptyReturnsDefault() {
        assertEquals(ValidationUtils.DEFAULT_GRADE, ValidationUtils.parseTargetGrade(""));
    }

    @Test
    public void parseTargetGrade_validMin() {
        assertEquals(1, ValidationUtils.parseTargetGrade("1"));
    }

    @Test
    public void parseTargetGrade_validMax() {
        assertEquals(18, ValidationUtils.parseTargetGrade("18"));
    }

    @Test
    public void parseTargetGrade_midValue() {
        assertEquals(8, ValidationUtils.parseTargetGrade("8"));
    }

    @Test(expected = IllegalArgumentException.class)
    public void parseTargetGrade_zeroThrows() {
        ValidationUtils.parseTargetGrade("0");
    }

    @Test(expected = IllegalArgumentException.class)
    public void parseTargetGrade_negativeThrows() {
        ValidationUtils.parseTargetGrade("-1");
    }

    @Test(expected = IllegalArgumentException.class)
    public void parseTargetGrade_tooHighThrows() {
        ValidationUtils.parseTargetGrade("19");
    }

    @Test(expected = IllegalArgumentException.class)
    public void parseTargetGrade_nonNumericThrows() {
        ValidationUtils.parseTargetGrade("abc");
    }

    @Test
    public void isInputValid_nullReturnsFalse() {
        assertFalse(ValidationUtils.isInputValid(null));
    }

    @Test
    public void isInputValid_emptyReturnsFalse() {
        assertFalse(ValidationUtils.isInputValid(""));
    }

    @Test
    public void isInputValid_whitespaceReturnsFalse() {
        assertFalse(ValidationUtils.isInputValid("   "));
    }

    @Test
    public void isInputValid_validTextReturnsTrue() {
        assertTrue(ValidationUtils.isInputValid("Hello world"));
    }
}
