# VOXMETRIK

## Music Analytics Platform

Real-time Spotify music data analytics powered by FastAPI + DuckDB

### Tech Stack

- **Frontend**: Angular 18 Standalone Components
- **Backend**: FastAPI + DuckDB
- **Data Source**: Spotify API
- **Styling**: CSS3 + CSS Variables

### Installation

```bash
npm install
ng serve
```

### Build

```bash
ng build --prod
```

### Project Structure

```
src/
├── app/
│   ├── features/          # Feature modules
│   ├── shared/            # Shared components & services
│   ├── core/              # Core guards & interceptors
│   ├── layouts/           # Layout components
│   └── app.routes.ts      # Route configuration
├── assets/                # Images & static files
├── environments/          # Environment configs
├── index.html             # HTML entry point
├── main.ts               # Bootstrap file
└── styles.css            # Global styles
```

### Features

- Dashboard with real-time KPIs
- Artist analytics
- Track analysis with audio features
- Genre distribution
- Audio features correlation
- Trending tracks & artists
- Advanced analytics
- ETL Pipeline monitoring
- Data explorer
- Comparative analysis

### License

MIT
