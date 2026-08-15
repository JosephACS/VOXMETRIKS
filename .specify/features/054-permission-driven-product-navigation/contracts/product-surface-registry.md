# Product surface registry contract

Each surface declares:

```ts
interface ProductSurfaceDefinition {
  id: string;
  labelKey: string;
  iconId: string;
  path: string;
  spaces: readonly SpaceKind[];
  organizationTier?: 'onboarding' | 'operational';
  capability?: string;
  staffCapability?: string;
  platformRole?: string;
  contextGroup?: string;
  order: number;
}
```

The evaluator receives only hydrated facts:

```ts
interface ProductSurfaceContext {
  ready: boolean;
  activeSpace: SpaceKind;
  organizationId?: number;
  organizationTier?: 'onboarding' | 'operational';
  permissions: ReadonlySet<string>;
  artistCapabilities: ReadonlySet<string>;
  staffCapabilities: ReadonlySet<string>;
  platformRoles: ReadonlySet<string>;
}
```

Rules:

1. `ready=false` never returns privileged surfaces.
2. All declared constraints are conjunctive.
3. Missing capability data fails closed.
4. The same result drives menu items and contextual tabs.
5. Route and backend authorization remain independent and authoritative.
6. No username, email, demo label or presentation flag is an input.
