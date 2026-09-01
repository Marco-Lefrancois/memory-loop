export const EnvProtection = async () => {
  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool === "read" && (output.args?.filePath?.includes(".env") || output.args?.path?.includes(".env"))) {
        throw new Error("Sécurité mLoop : Accès direct au fichier .env interdit. Utilisez les variables d'environnement ou ~/.secrets/");
      }
    }
  };
};
