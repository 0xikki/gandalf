import { useState, useCallback } from 'react';

export type ValidationRule<T = any> = {
  required?: {
    value: boolean;
    message: string;
  };
  pattern?: {
    value: RegExp;
    message: string;
  };
  minLength?: {
    value: number;
    message: string;
  };
  maxLength?: {
    value: number;
    message: string;
  };
  min?: {
    value: number;
    message: string;
  };
  max?: {
    value: number;
    message: string;
  };
  validate?: {
    value: (value: T) => boolean | Promise<boolean>;
    message: string;
  };
  custom?: {
    isValid: (value: T) => boolean | Promise<boolean>;
    message: string;
  };
  deps?: string[];
};

export type ValidationRules<T extends Record<string, any>> = {
  [K in keyof T]?: ValidationRule<T[K]>;
};

export type ValidationErrors<T> = {
  [K in keyof T]?: string;
};

export interface UseFormValidationOptions<T extends Record<string, any>> {
  initialValues: T;
  validationRules: ValidationRules<T>;
  validateOnChange?: boolean;
  validateOnBlur?: boolean;
  onSubmit?: (values: T) => void | Promise<void>;
}

export function useFormValidation<T extends Record<string, any>>({
  initialValues,
  validationRules,
  validateOnChange = true,
  validateOnBlur = true,
  onSubmit,
}: UseFormValidationOptions<T>) {
  const [values, setValues] = useState<T>(initialValues);
  const [errors, setErrors] = useState<ValidationErrors<T>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [touched, setTouched] = useState<Record<keyof T, boolean>>({} as Record<keyof T, boolean>);

  const validateField = useCallback(async (
    name: keyof T,
    value: any,
    rules?: ValidationRule,
    allValues: T = values
  ): Promise<string | undefined> => {
    if (!rules) return undefined;

    // Required validation
    if (rules.required?.value && !value) {
      return rules.required.message;
    }

    // Skip other validations if value is empty and not required
    if (!value && !rules.required?.value) {
      return undefined;
    }

    // Pattern validation
    if (rules.pattern?.value && !rules.pattern.value.test(value)) {
      return rules.pattern.message;
    }

    // Min length validation
    if (rules.minLength?.value && String(value).length < rules.minLength.value) {
      return rules.minLength.message;
    }

    // Max length validation
    if (rules.maxLength?.value && String(value).length > rules.maxLength.value) {
      return rules.maxLength.message;
    }

    // Min value validation
    if (rules.min?.value && Number(value) < rules.min.value) {
      return rules.min.message;
    }

    // Max value validation
    if (rules.max?.value && Number(value) > rules.max.value) {
      return rules.max.message;
    }

    // Custom validation
    if (rules.custom?.isValid) {
      const isValid = await Promise.resolve(rules.custom.isValid(value));
      if (!isValid) {
        return rules.custom.message;
      }
    }

    // Validate with dependencies
    if (rules.validate?.value) {
      const isValid = await Promise.resolve(rules.validate.value(value));
      if (!isValid) {
        return rules.validate.message;
      }
    }

    return undefined;
  }, [values]);

  const validateForm = useCallback(async (data: T = values): Promise<ValidationErrors<T>> => {
    const validationPromises = Object.keys(validationRules).map(async (key) => {
      const fieldName = key as keyof T;
      const error = await validateField(
        fieldName,
        data[fieldName],
        validationRules[fieldName],
        data
      );
      return { fieldName, error };
    });

    const validationResults = await Promise.all(validationPromises);
    const newErrors: ValidationErrors<T> = {};

    validationResults.forEach(({ fieldName, error }) => {
      if (error) {
        newErrors[fieldName] = error;
      }
    });

    return newErrors;
  }, [validateField, validationRules, values]);

  const handleChange = useCallback(async (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = event.target;
    const newValues = { ...values, [name]: value };
    setValues(newValues);

    if (validateOnChange && touched[name as keyof T]) {
      const error = await validateField(
        name as keyof T,
        value,
        validationRules[name as keyof T],
        newValues
      );
      setErrors(prev => ({
        ...prev,
        [name]: error,
      }));
    }
  }, [validateField, validateOnChange, touched, validationRules, values]);

  const handleBlur = useCallback(async (
    event: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name } = event.target;
    setTouched(prev => ({
      ...prev,
      [name]: true,
    }));

    if (validateOnBlur) {
      const error = await validateField(
        name as keyof T,
        values[name as keyof T],
        validationRules[name as keyof T]
      );
      setErrors(prev => ({
        ...prev,
        [name]: error,
      }));
    }
  }, [validateField, validateOnBlur, values, validationRules]);

  const handleSubmit = useCallback(async (
    event?: React.FormEvent<HTMLFormElement>
  ) => {
    if (event) {
      event.preventDefault();
    }

    setIsSubmitting(true);
    const newErrors = await validateForm();
    setErrors(newErrors);

    if (Object.keys(newErrors).length === 0 && onSubmit) {
      try {
        await onSubmit(values);
      } catch (error) {
        // Handle submission error
        console.error('Form submission error:', error);
      }
    }
    setIsSubmitting(false);
  }, [validateForm, onSubmit, values]);

  const reset = useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setTouched({} as Record<keyof T, boolean>);
    setIsSubmitting(false);
  }, [initialValues]);

  const setFieldValue = useCallback(async (
    name: keyof T,
    value: any,
    shouldValidate = true
  ) => {
    const newValues = { ...values, [name]: value };
    setValues(newValues);

    if (shouldValidate && validationRules[name]) {
      const error = await validateField(
        name,
        value,
        validationRules[name],
        newValues
      );
      setErrors(prev => ({
        ...prev,
        [name]: error,
      }));
    }
  }, [validateField, validationRules, values]);

  return {
    values,
    errors,
    touched,
    isSubmitting,
    handleChange,
    handleBlur,
    handleSubmit,
    reset,
    setFieldValue,
    validateField,
    validateForm,
  };
} 