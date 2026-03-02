import js from "@eslint/js";
import nextPlugin from "@next/eslint-plugin-next";
import tseslint from "typescript-eslint";

const eslintConfig = [
  {
    ignores: [
      ".next/**",
      "node_modules/**",
      "public/**",
      "playwright-report/**",
      "test-results/**",
    ],
  },
  js.configs.recommended,
  nextPlugin.configs.recommended,
  ...tseslint.configs.recommended,
  {
    rules: {
      // TypeScript handles these better than ESLint
      "no-unused-vars": "off",
      "no-undef": "off",
      // Relax TS rules for pragmatic development
      "@typescript-eslint/no-unused-vars": ["warn", { argsIgnorePattern: "^_", varsIgnorePattern: "^_" }],
      "@typescript-eslint/no-explicit-any": "warn",
      "@typescript-eslint/no-empty-object-type": "off",
      "@typescript-eslint/no-require-imports": "off",
    },
  },
];

export default eslintConfig;
