# GitHub Configuration

## CI/CD Pipeline

Un seul workflow simple et efficace : **`ci.yml`**

### Qu'est-ce qu'il fait?

1. **Backend Tests** - Exécute les tests Python avec coverage
2. **Code Quality** - Vérifie le formatage et la qualité du code
3. **Frontend Build** - Construit et teste le frontend
4. **Status Check** - Vérifie que tout est OK avant production

### Pas de:
- ❌ Dependabot (gestion manuelle des dépendances)
- ❌ Security scanning (tu gères la sécurité)
- ❌ Release drafting (releases manuelles)
- ❌ Label management (labels manuels)
- ❌ Complexity analysis (trop optionnel)

### Philosophy
**"Simple is Beautiful, Zen Mentality"** 🧘

Un seul workflow = facile à comprendre = facile à maintenir = moins de crédits gratuits utilisés.

## À faire manuellement

- Mises à jour de dépendances (npm/pip update)
- Releases (git tag + GitHub release)
- Documentation (commit manuel)
- Review de sécurité (vous êtes responsable)
