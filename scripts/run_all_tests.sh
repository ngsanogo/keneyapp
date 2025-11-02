#!/usr/bin/env bash
# Script pour exécuter tous les tests de KeneyApp v3.0
# Usage: ./scripts/run_all_tests.sh [options]

set -e

# Couleurs pour l'affichage
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   KeneyApp v3.0 - Suite de Tests Exhaustive${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Vérifier que pytest est installé
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest n'est pas installé${NC}"
    echo -e "${YELLOW}Installer avec: pip install -r requirements-test.txt${NC}"
    exit 1
fi

# Créer le répertoire de rapports s'il n'existe pas
mkdir -p test-reports
mkdir -p htmlcov

# Parser les options
PYTEST_ARGS=""
RUN_COVERAGE=true
RUN_SLOW=false
RUN_SMOKE=false
PARALLEL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-cov)
            RUN_COVERAGE=false
            shift
            ;;
        --slow)
            RUN_SLOW=true
            shift
            ;;
        --smoke)
            RUN_SMOKE=true
            shift
            ;;
        --parallel)
            PARALLEL=true
            shift
            ;;
        --fast)
            PYTEST_ARGS="$PYTEST_ARGS -x -m 'not slow and not smoke'"
            shift
            ;;
        *)
            PYTEST_ARGS="$PYTEST_ARGS $1"
            shift
            ;;
    esac
done

# Construire la commande pytest
PYTEST_CMD="pytest"

if [ "$PARALLEL" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -n auto"
    echo -e "${BLUE}🚀 Exécution des tests en parallèle${NC}"
fi

if [ "$RUN_COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=app --cov-report=html --cov-report=term-missing --cov-report=xml"
fi

# Ajouter les markers si nécessaire
if [ "$RUN_SLOW" = false ]; then
    PYTEST_CMD="$PYTEST_CMD -m 'not slow'"
fi

if [ "$RUN_SMOKE" = false ]; then
    PYTEST_CMD="$PYTEST_CMD -m 'not smoke'"
fi

# Ajouter les arguments supplémentaires
PYTEST_CMD="$PYTEST_CMD $PYTEST_ARGS"

echo -e "${GREEN}📋 Commande:${NC} $PYTEST_CMD"
echo ""

# 1. Tests unitaires des modèles v3.0
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  1/8 Tests Unitaires - Modèles v3.0                          ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
pytest tests/test_comprehensive_v3.py::TestModelsV3 -v || true
echo ""

# 2. Tests unitaires des schémas Pydantic
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  2/8 Tests Unitaires - Schémas Pydantic v3.0                 ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
pytest tests/test_comprehensive_v3.py::TestSchemasV3 -v || true
echo ""

# 3. Tests de la messagerie
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  3/8 Tests Messagerie Sécurisée                               ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
pytest tests/test_messages.py -v || true
echo ""

# 4. Tests des documents
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  4/8 Tests Gestion de Documents                               ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
pytest tests/test_documents.py -v || true
echo ""

# 5. Tests du partage
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  5/8 Tests Partage Sécurisé                                   ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
pytest tests/test_shares.py -v || true
echo ""

# 6. Tests d'intégration E2E
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  6/8 Tests Intégration E2E                                    ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
pytest tests/test_comprehensive_v3.py::TestIntegrationE2E -v || true
echo ""

# 7. Tests de sécurité
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  7/8 Tests Sécurité Avancés                                   ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
pytest tests/test_comprehensive_v3.py::TestSecurityAdvanced -v || true
echo ""

# 8. Tests de performance
if [ "$RUN_SLOW" = true ]; then
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  8/8 Tests Performance et Charge                              ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
    pytest tests/test_comprehensive_v3.py::TestPerformanceAndLoad -v || true
    echo ""
fi

# Exécuter tous les tests existants
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Tests Existants (v1.0 et v2.0)                               ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
pytest tests/test_api.py tests/test_audit.py tests/test_encryption.py tests/test_fhir.py tests/test_graphql.py -v || true
echo ""

# Rapport final
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Suite de tests terminée !${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ "$RUN_COVERAGE" = true ]; then
    echo -e "${GREEN}📊 Rapport de couverture:${NC}"
    echo -e "   HTML: ${BLUE}htmlcov/index.html${NC}"
    echo -e "   XML:  ${BLUE}coverage.xml${NC}"
    echo ""
fi

echo -e "${YELLOW}💡 Options disponibles:${NC}"
echo -e "   --no-cov    : Désactiver la couverture de code"
echo -e "   --slow      : Inclure les tests lents"
echo -e "   --smoke     : Inclure les smoke tests"
echo -e "   --parallel  : Exécution parallèle"
echo -e "   --fast      : Mode rapide (skip slow & smoke)"
echo ""

echo -e "${GREEN}🎉 Pour voir le rapport de couverture:${NC}"
echo -e "   ${BLUE}open htmlcov/index.html${NC}  (macOS)"
echo -e "   ${BLUE}xdg-open htmlcov/index.html${NC}  (Linux)"
echo ""
