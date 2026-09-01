# ADR-0314 : Gouvernance des Notifications Push (Consentement & Nécessité)

**Statut** : Approuvé
**Date** : 2026-08-12
**Auteur** : Orchestrateur mLoop (via Erwan/PO Metro)

## Contexte
L'application Metro nécessite une gestion fine des notifications Push. Pour garantir à la fois l'engagement utilisateur et la conformité Privacy (OneTrust), il a été décidé que les notifications Push sont considérées comme "Strictement Nécessaires" à la proposition de valeur métier, tout en maintenant un contrôle total de l'utilisateur (Opt-in/Opt-out).

## Décision
Il est acté que le système de notification Push ne sera pas traité comme une fonctionnalité accessoire, mais comme un canal de communication essentiel. Le consentement de l'utilisateur sera traité en deux couches :
1.  **Couche Applicative** : Gestion du consentement dans les paramètres de l'application via `IUserSettingsRepository`.
2.  **Couche Système** : Permission native de l'appareil (OS).

## Conséquences
- **Développement** : Tout nouveau développement lié aux notifications Push doit utiliser le `IPushNotificationService` existant et respecter le cycle de vie de permission défini.
- **Conformité** : La justification "Strictement Nécessaire" doit être documentée dans chaque récit métier (`User Story`) impactant ce canal.
- **Architecture** : Le code source (notamment `Food/Views/AccountViews/NotificationSettingsView.xaml.cs`) doit être audité lors de tout changement pour garantir l'intégrité de ce consentement.

## Scénarios Gherkin (Référence)
- **Nominal** : L'utilisateur active les notifications dans l'application -> La permission système est demandée -> Le consentement est enregistré.
- **Exception** : L'utilisateur refuse la permission système -> L'application informe l'utilisateur sur la limitation de service.
