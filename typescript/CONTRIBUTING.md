# Contributing to CPM (TypeScript SDK)

Thank you for your interest in contributing to CPM! This document provides guidelines for contributing to the TypeScript SDK.

## Getting Started

### Prerequisites

- Node.js 18.0.0 or higher
- npm, yarn, or pnpm
- Git

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/transilienceai/cpm.git
   cd cpm/typescript
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Build the project:
   ```bash
   npm run build
   ```

4. Run tests:
   ```bash
   npm test
   ```

## Project Structure

```
typescript/
├── src/
│   ├── index.ts           # Main entry point
│   ├── cli.ts             # CLI entry point
│   ├── schemas/           # Zod schemas
│   │   ├── cpm.ts
│   │   ├── project.ts
│   │   └── component.ts
│   ├── core/              # Core functionality
│   │   ├── config.ts      # Config loading/saving
│   │   ├── resolver.ts    # Dependency resolution
│   │   └── linker.ts      # Symlink management
│   ├── commands/          # CLI commands
│   │   ├── init.ts
│   │   ├── create.ts
│   │   ├── add.ts
│   │   └── ...
│   └── utils/             # Utilities
│       └── output.ts
├── tests/                 # Test files
│   ├── schemas.test.ts
│   ├── config.test.ts
│   ├── resolver.test.ts
│   └── linker.test.ts
├── package.json
└── tsconfig.json
```

## Development Workflow

### Making Changes

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following the coding standards

3. Add tests for new functionality

4. Run tests and linting:
   ```bash
   npm test
   npm run lint
   ```

5. Build to check for TypeScript errors:
   ```bash
   npm run build
   ```

6. Commit your changes:
   ```bash
   git commit -m "feat: add new feature"
   ```

7. Push and create a pull request

### Coding Standards

#### TypeScript Style

- Use strict TypeScript (`strict: true` in tsconfig)
- Use explicit return types for functions
- Use `type` imports for type-only imports
- Avoid `any` - use `unknown` if type is truly unknown

```typescript
// Good
export async function loadConfig(path: string): Promise<Config> {
  // ...
}

// Bad
export async function loadConfig(path) {
  // ...
}
```

#### Naming Conventions

- Functions: `camelCase`
- Types/Interfaces: `PascalCase`
- Constants: `UPPER_SNAKE_CASE` or `camelCase`
- Files: `kebab-case.ts` or `camelCase.ts`

#### Documentation

- All public functions must have JSDoc comments
- Include `@param` and `@returns` tags

```typescript
/**
 * Load CPM configuration from a repository root.
 * @param repoRoot - Path to the repository root
 * @returns The parsed CPM configuration
 * @throws Error if cpm.json is not found
 */
export async function loadCpmConfig(repoRoot: string): Promise<CpmConfig> {
  // ...
}
```

#### Testing

- Write tests for all new functionality
- Use descriptive test names
- Test both success and error cases

```typescript
describe("loadCpmConfig", () => {
  it("should load valid config", async () => {
    // ...
  });

  it("should throw for missing config", async () => {
    await expect(loadCpmConfig(testDir)).rejects.toThrow();
  });
});
```

## Pull Request Guidelines

### Before Submitting

- [ ] Tests pass (`npm test`)
- [ ] Build succeeds (`npm run build`)
- [ ] Code follows style guidelines
- [ ] Documentation updated if needed

### PR Title Format

Use conventional commits:

- `feat: Add new feature`
- `fix: Fix bug in X`
- `docs: Update documentation`
- `refactor: Refactor X module`
- `test: Add tests for Y`
- `chore: Update dependencies`

### PR Description

Include:

1. **Summary**: What does this PR do?
2. **Motivation**: Why is this change needed?
3. **Testing**: How was it tested?
4. **Breaking Changes**: Any breaking changes?

## Scripts

| Script | Description |
|--------|-------------|
| `npm run build` | Build TypeScript to JavaScript |
| `npm run dev` | Watch mode for development |
| `npm test` | Run tests |
| `npm run test:watch` | Run tests in watch mode |
| `npm run lint` | Run ESLint |
| `npm run format` | Format with Prettier |

## Reporting Issues

### Bug Reports

Include:

- CPM version (`cpm --version`)
- Node.js version (`node --version`)
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages

### Feature Requests

Include:

- Use case description
- Proposed solution
- Alternatives considered

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

<p align="center">
  Thank you for contributing to CPM!
</p>

<p align="center">
  <a href="https://transilience.ai"><img src="../docs/logo/transilience.png" alt="Transilience.ai" height="20" /></a>
</p>
