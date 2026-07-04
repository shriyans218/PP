# Deploy Pantry Pulse to Vercel

This repo includes a Vercel-ready static dashboard in `public/`.

## One-time Login

```bash
npx vercel login
```

Choose your preferred login method in the browser or terminal prompt.

## Deploy

```bash
npx vercel --prod --yes
```

If you deploy from GitHub instead:

1. Push this `pantry-pulse` folder to a GitHub repository.
2. Open Vercel and choose **Add New Project**.
3. Import the GitHub repository.
4. Keep the default static settings.
5. Deploy.

The Streamlit app remains available for local demos:

```bash
streamlit run app.py
```

The Vercel version serves `public/index.html` and `public/data.json`.
