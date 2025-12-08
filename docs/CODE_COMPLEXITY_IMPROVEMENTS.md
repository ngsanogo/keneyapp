# Code Complexity Improvements Roadmap

## Overview

This document tracks remaining code complexity violations (C901 - Cyclomatic Complexity) that require architectural refactoring beyond simple extraction.

**Status**: 6 violations remaining, scheduled for future releases
**Last Updated**: 2024

## Remaining C901 Violations

### 1. `get_patient_medical_history` (app/routers/patients.py:769)
- **Complexity**: 22 (highest)
- **Issue**: Multiple nested conditionals for filtering, pagination, encryption
- **Suggested Refactoring**:
  - Extract filter building into separate service method
  - Move encryption handling to service layer
  - Create `PatientHistoryFilter` helper class

### 2. `websocket_endpoint` (app/routers/websocket.py:63)
- **Complexity**: 16
- **Issue**: Mixed concerns (auth, message routing, error handling)
- **Suggested Refactoring**:
  - Create `WebSocketManager` class for message handling
  - Extract auth logic to dependency
  - Move routing to separate handler functions

### 3. `should_send_notification` (app/services/notification_service.py:353)
- **Complexity**: 11
- **Issue**: Multiple conditional checks for notification preferences
- **Suggested Refactoring**:
  - Create `NotificationPreferenceChecker` class
  - Extract each condition to separate validator method
  - Use decorator pattern for preference checks

### 4. `send_notification` (app/services/notification_service.py:459)
- **Complexity**: 11
- **Issue**: Multiple channel handling and error recovery logic
- **Suggested Refactoring**:
  - Create strategy pattern for each notification channel
  - Extract retry logic to separate decorator
  - Use chain of responsibility for channel selection

### 5. `list_patients_advanced` (app/services/patient_service.py:310)
- **Complexity**: 20
- **Issue**: Complex filtering, sorting, pagination logic
- **Suggested Refactoring**:
  - Create `PatientQueryBuilder` class for query construction
  - Extract filter building to separate service
  - Move pagination to utility function

### 6. `get_patient_care_recommendations` (app/services/recommendation_service.py:48)
- **Complexity**: 11
- **Issue**: Multiple business rules for recommendation logic
- **Suggested Refactoring**:
  - Create recommendation rule engines
  - Extract each rule to separate validator class
  - Use rule evaluation engine pattern

## Refactoring Strategy

### Phase 1: Quick Wins (Already Done)
- ✅ Extract validation functions from `validate_production_settings`
- ✅ Extract batch operation helpers from `batch_create_patients` and `batch_update_patients`
- ✅ Remove unused imports and fix style violations
- ✅ Reduce overall violations from 59 to 6 (90% improvement)

### Phase 2: Service Layer Improvements (Recommended Next)
- Extract query building logic to service classes
- Create validation/checker classes for business rules
- Implement strategy patterns for multi-branch logic

### Phase 3: Architectural Improvements
- Consider event-driven architecture for notifications
- Implement query object pattern for complex filters
- Create domain-specific language for recommendations

## Impact Assessment

| Function | Current Score | Target | Effort | Risk |
|----------|---|---|---|---|
| get_patient_medical_history | 22 | <10 | Medium | Low |
| list_patients_advanced | 20 | <10 | Medium | Low |
| websocket_endpoint | 16 | <10 | High | Medium |
| validate_production_settings | ~~16~~ | ✅ 8 | Low | Low |
| send_notification | 11 | <8 | High | High |
| should_send_notification | 11 | <8 | High | High |
| get_patient_care_recommendations | 11 | <8 | Medium | Medium |
| batch_create_patients | ~~13~~ | ✅ 8 | Low | Low |
| batch_update_patients | ~~12~~ | ✅ 6 | Low | Low |

## Tools & Patterns

### Recommended Patterns
1. **Query Object Pattern** - For complex database queries
2. **Strategy Pattern** - For multiple channel/rule handling
3. **Builder Pattern** - For query/filter construction
4. **Validator Pattern** - For rule checking
5. **Chain of Responsibility** - For sequential processing

### Testing Requirements
- Unit tests for each extracted function
- Integration tests for full workflows
- Performance regression tests for query building

## Timeline

- **Q1 2024**: Complete Phase 1 (Done) ✅
- **Q2 2024**: Phase 2 recommendations
- **Q3 2024+**: Phase 3 architectural improvements

## Notes

- Current flake8 compliance: 90% improvement (59 → 6 violations)
- All critical style violations resolved
- C901 violations have lower impact on maintainability than style violations
- Recommend addressing in priority order: get_patient_medical_history, list_patients_advanced
