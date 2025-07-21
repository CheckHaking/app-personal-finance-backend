# Personal Finance App - Backend

This project is the backend API for a personal finance application, built with Django and Django REST Framework.

## Core Architectural Principles

This project follows an **API-First Design** approach. We first define the "contract" between the backend and the frontend—the API endpoints and data structures—before implementing the logic. This ensures a clear separation of concerns and allows for parallel development.

The architecture is guided by key software design principles, primarily the **Single Responsibility Principle (SRP)**.

## Application Structure

To maintain a clean, organized, and scalable codebase, the project is divided into distinct Django "apps". Each app has a single, well-defined responsibility.

### 1. `users` App

-   **Responsibility:** Manages everything related to user identity, authentication, and profiles.
-   **Core Models:**
    -   `User`: The custom user model for authentication.
    -   `Profile`: Stores additional user-specific data like default currency.

### 2. `core` App

-   **Responsibility:** Manages the core financial logic of the application. All models related to handling money and financial activities reside here due to their high functional cohesion.
-   **Core Models:**
    -   **`Account`**: The central model representing any place a user has money or debt (e.g., cash wallet, bank account, credit card). This powerful model abstracts away the need for separate `Card` or `Debt` apps.
    -   **`Category`**: A support model used to classify transactions (e.g., "Food", "Transport", "Salary").
    -   **`Transaction`**: Represents any income or expense movement associated with an `Account`.
    -   **`Transfer`**: Represents the movement of funds between two of the user's `Accounts`.

This structure ensures that related logic is grouped together, making the project easier to understand, maintain, and extend in the future.
