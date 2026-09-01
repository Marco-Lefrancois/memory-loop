# Modèles NMedia Cloud Disponibles

*Cette liste est interrogée et validée dynamiquement depuis `api-ia.nmedia.ca` (endpoints `/v1/models` et `/v1/model/info`).*

| Légende Statut | Description |
| :--- | :--- |
| 🟢 **Actif** | Modèle fonctionnel et validé par test d'appel API |
| 🔴 **Inactif / Inaccessible** | Indisponible (404, 401 ou erreur backend provider) |

## Anthropic (Claude)
| Modèle | Statut | Coût Input (par 1M tokens) | Coût Output (par 1M tokens) | Context Max In | Max Output |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `claude-opus-4.7` | 🟢 Actif | $5.00 / 1M | $25.00 / 1M | 1000000 | 128000 |
| `claude-opus-4.7-thinking` | 🔴 Inactif | $5.00 / 1M | $25.00 / 1M | 1000000 | 128000 |
| `claude-opus-4.6` | 🟢 Actif | $5.00 / 1M | $25.00 / 1M | 1000000 | 128000 |
| `claude-opus-4.6-thinking` | 🔴 Inactif | $5.00 / 1M | $25.00 / 1M | 1000000 | 128000 |
| `claude-sonnet-4.6` | 🟢 Actif | $3.00 / 1M | $15.00 / 1M | 1000000 | 64000 |
| `claude-sonnet-4.6-thinking` | 🔴 Inactif | $3.00 / 1M | $15.00 / 1M | 1000000 | 64000 |
| `claude-sonnet-4.5` | 🟢 Actif | $3.00 / 1M | $15.00 / 1M | 200000 | 64000 |
| `claude-sonnet-4.5-thinking` | 🔴 Inactif | $3.00 / 1M | $15.00 / 1M | 200000 | 64000 |
| `claude-haiku-4.5` | 🟢 Actif | $1.00 / 1M | $5.00 / 1M | 200000 | 64000 |
| `claude-haiku-4.5-thinking` | 🔴 Inactif | $1.00 / 1M | $5.00 / 1M | 200000 | 64000 |
| `claude-3-7-sonnet` | 🔴 Inactif | $3.00 / 1M | $15.00 / 1M | 200000 | 64000 |
| `claude-3-5-sonnet-v2` | 🔴 Inactif | N/A | N/A | N/A | N/A |
| `claude-sonnet-4-5-20250929` | 🟢 Actif | $3.00 / 1M | $15.00 / 1M | 200000 | 64000 |
| `claude-haiku-4-5-20251001` | 🟢 Actif | $1.00 / 1M | $5.00 / 1M | 200000 | 64000 |
| `claude-opus-4-6` | 🟢 Actif | $5.00 / 1M | $25.00 / 1M | 1000000 | 128000 |
| `claude-opus-4-7` | 🟢 Actif | $5.00 / 1M | $25.00 / 1M | 1000000 | 128000 |
| `claude-sonnet-4-6` | 🟢 Actif | $3.00 / 1M | $15.00 / 1M | 1000000 | 64000 |
| `claude-haiku-4-5` | 🟢 Actif | $1.00 / 1M | $5.00 / 1M | 200000 | 64000 |

## OpenAI (GPT)
| Modèle | Statut | Coût Input (par 1M tokens) | Coût Output (par 1M tokens) | Context Max In | Max Output |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `gpt-5.5` | 🟢 Actif | $5.00 / 1M | $30.00 / 1M | 1050000 | 128000 |
| `gpt-5.5-thinking` | 🟢 Actif | $5.00 / 1M | $30.00 / 1M | 1050000 | 128000 |
| `gpt-5.4` | 🟢 Actif | $2.50 / 1M | $15.00 / 1M | 1050000 | 128000 |
| `gpt-5.4-thinking` | 🟢 Actif | $2.50 / 1M | $15.00 / 1M | 1050000 | 128000 |
| `gpt-5.4-mini` | 🟢 Actif | $0.75 / 1M | $4.50 / 1M | 1050000 | 128000 |
| `gpt-5.4-nano` | 🟢 Actif | $0.20 / 1M | $1.25 / 1M | 1050000 | 128000 |
| `gpt-5.3-codex` | 🟢 Actif | $1.75 / 1M | $14.00 / 1M | 272000 | 128000 |
| `gpt-5.2` | 🟢 Actif | $1.75 / 1M | $14.00 / 1M | 272000 | 128000 |
| `gpt-5.2-thinking` | 🟢 Actif | $1.75 / 1M | $14.00 / 1M | 272000 | 128000 |
| `gpt-5.2-codex` | 🔴 Inactif | $1.75 / 1M | $14.00 / 1M | 272000 | 128000 |
| `gpt-5.2-azure-canada` | 🟢 Actif | $1.75 / 1M | $14.00 / 1M | 272000 | 128000 |
| `gpt-5-mini` | 🟢 Actif | $0.25 / 1M | $2.00 / 1M | 272000 | 128000 |
| `gpt-5-nano` | 🟢 Actif | $0.05 / 1M | $0.40 / 1M | 272000 | 128000 |
| `gpt-5-mini-azure-canada` | 🟢 Actif | $0.25 / 1M | $2.00 / 1M | 272000 | 128000 |
| `gpt-4.1-nano` | 🟢 Actif | $0.10 / 1M | $0.40 / 1M | 1047576 | 32768 |
| `gpt-4o` | 🟢 Actif | $2.50 / 1M | $10.00 / 1M | 128000 | 16384 |

## Google (Gemini)
| Modèle | Statut | Coût Input (par 1M tokens) | Coût Output (par 1M tokens) | Context Max In | Max Output |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `gemini-3.5-flash` | 🟢 Actif | $1.50 / 1M | $9.00 / 1M | 1000000 | 65536 |
| `gemini-3.1-pro-preview` | 🟢 Actif | $2.00 / 1M | $12.00 / 1M | 1048576 | 65536 |
| `gemini-3.1-pro-preview-thinking` | 🟢 Actif | $2.00 / 1M | $12.00 / 1M | 1048576 | 65536 |
| `gemini-3.1-flash-lite` | 🟢 Actif | $0.25 / 1M | $1.50 / 1M | 1048576 | 65536 |
| `gemini-3.1-flash-lite-thinking` | 🟢 Actif | $0.25 / 1M | $1.50 / 1M | 1048576 | 65536 |
| `gemini-3-pro-image-preview` | 🟢 Actif | $2.00 / 1M | $12.00 / 1M | 65536 | 32768 |
| `gemini-3-flash-preview` | 🟢 Actif | $0.50 / 1M | $3.00 / 1M | 1048576 | 65535 |
| `gemini-3-flash-preview-thinking` | 🟢 Actif | $0.50 / 1M | $3.00 / 1M | 1048576 | 65535 |
| `gemini-2.5-pro` | 🟢 Actif | $1.25 / 1M | $10.00 / 1M | 1048576 | 65535 |
| `gemini-2.5-flash` | 🟢 Actif | $0.30 / 1M | $2.50 / 1M | 1048576 | 65535 |
| `gemini-2.5-flash-image` | 🔴 Inactif | $0.00 / 1M | $0.00 / 1M | N/A | N/A |
| `gemini-2.0-flash` | 🔴 Inactif | $0.10 / 1M | $0.40 / 1M | 1048576 | 8192 |

## DeepSeek
| Modèle | Statut | Coût Input (par 1M tokens) | Coût Output (par 1M tokens) | Context Max In | Max Output |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `deepseek-r1` | 🟢 Actif | $0.00 / 1M | $0.00 / 1M | 128000 | 8192 |

## Perplexity (Recherche / Sonar)
| Modèle | Statut | Coût Input (par 1M tokens) | Coût Output (par 1M tokens) | Context Max In | Max Output |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `perplexity-sonar-deep-research` | 🔴 Inactif | $2.00 / 1M | $8.00 / 1M | 128000 | N/A |
| `perplexity-sonar-reasoning-pro` | 🟢 Actif | $2.00 / 1M | $8.00 / 1M | 128000 | N/A |
| `perplexity-sonar-pro` | 🟢 Actif | $3.00 / 1M | $15.00 / 1M | 200000 | 8000 |

## Modèles Spécialisés (Codestral, Image, Audio)
| Modèle | Statut | Coût Input (par 1M tokens) | Coût Output (par 1M tokens) | Context Max In | Max Output |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `codestral-2501` | 🟢 Actif | N/A | N/A | N/A | N/A |
| `mistral-ocr` | 🔴 Inactif | $0.00 / 1M | $0.00 / 1M | N/A | N/A |
| `mistral-voxtral-mini-2602` | 🔴 Inactif | $0.00 / 1M | $0.00 / 1M | N/A | N/A |
| `gpt-image-1` | 🔴 Inactif | $5.00 / 1M | $0.00 / 1M | N/A | N/A |
| `gpt-image-1.5` | 🔴 Inactif | $5.00 / 1M | $10.00 / 1M | N/A | N/A |
| `gpt-4o-transcribe` | 🔴 Inactif | $2.50 / 1M | $10.00 / 1M | 16000 | 2000 |
| `gpt-4o-mini-transcribe` | 🔴 Inactif | $1.25 / 1M | $5.00 / 1M | 16000 | 2000 |
| `gpt-4o-transcribe-diarize` | 🔴 Inactif | $2.50 / 1M | $10.00 / 1M | 16000 | 2000 |
| `whisper-1` | 🔴 Inactif | $0.00 / 1M | $0.00 / 1M | N/A | N/A |
| `elevenlabs-scribe-v2` | 🔴 Inactif | $0.00 / 1M | $0.00 / 1M | N/A | N/A |
| `tts-1` | 🔴 Inactif | $0.00 / 1M | $0.00 / 1M | N/A | N/A |
| `text-embedding-3-small` | 🔴 Inactif | $0.02 / 1M | $0.00 / 1M | 8191 | N/A |

## Routages et Alias Globaux
| Modèle | Statut | Coût Input (par 1M tokens) | Coût Output (par 1M tokens) | Context Max In | Max Output |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `Recommandé` | 🟢 Actif | $0.50 / 1M | $3.00 / 1M | 1048576 | 65535 |
| `Économique` | 🟢 Actif | $0.25 / 1M | $2.00 / 1M | 272000 | 128000 |
| `Recherche web` | 🟢 Actif | $2.00 / 1M | $8.00 / 1M | 128000 | N/A |
| `Recherche web avancée` | 🔴 Inactif | $2.00 / 1M | $8.00 / 1M | 128000 | N/A |
| `Anthropic` | 🟢 Actif | $3.00 / 1M | $15.00 / 1M | 200000 | 64000 |
| `Canada (Azure)` | 🟢 Actif | $1.75 / 1M | $14.00 / 1M | 272000 | 128000 |
| `Canada (Azure) Économique` | 🔴 Inactif | N/A | N/A | N/A | N/A |
| `Automatique` | 🟢 Actif | $0.00 / 1M | $0.00 / 1M | N/A | N/A |
