# Formalizer High-level Design Doc

This project reproduces existing PDF forms in Typst using a tight LLM orchestration flow.

## Architecture

- Monorepo of Python and Typst modules with opinionated CLI for convenient usage
- Use `uv` project manager
- Use https://github.com/jbarrow/commonforms for robust form field extraction
- Add popular dependencies at your discretion
- Our goal is not 100% coverage of all forms. Our system should be opinionated and achieve nearly perfect reproductions of most conventional PDF forms.

### Components

- Formalizer-Typst

## The Formalizer-Typst Package

We should have a Typst package template with abstractions for form functionality.



## Workflow

### User Input

The user inputs:
- Package name (kebab-case)
- The original PDF form

### Package Setup

This phase programatically bootstraps a Typst package for reproducing the source form.

1. Duplicate a local Typst package template and configure the name and page size.
2. Convert the source form into an image as the background of the document.

### Form Field Extraction

This phase generates a JSON
