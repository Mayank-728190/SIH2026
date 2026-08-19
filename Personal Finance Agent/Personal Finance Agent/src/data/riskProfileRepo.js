import { readCSVFile } from './csvReader.js';

let riskCache = null;
let riskMap = null;

function loadRiskProfiles() {
  if (!riskCache) {
    console.log('[RiskProfileRepo] Loading risk_profiles.csv...');
    const raw = readCSVFile('risk_profiles.csv');
    riskCache = raw.map(r => ({
      ...r,
      Fraud_Flag: r.Fraud_Flag === 'True' || r.Fraud_Flag === 'true',
      Unusual_Login_Flag: r.Unusual_Login_Flag === 'True' || r.Unusual_Login_Flag === 'true',
      Geo_Anomaly_Flag: r.Geo_Anomaly_Flag === 'True' || r.Geo_Anomaly_Flag === 'true',
      Fraud_Risk_Score: Number(r.Fraud_Risk_Score || 0),
      Overall_Risk_Score: Number(r.Overall_Risk_Score || 0),
      Failed_Login_Count: Number(r.Failed_Login_Count || 0),
      Account_Takeover_Risk: Number(r.Account_Takeover_Risk || 0),
      High_Value_Transaction_Count: Number(r.High_Value_Transaction_Count || 0),
      Suspicious_Transaction_Count: Number(r.Suspicious_Transaction_Count || 0),
      Device_Trust_Score: Number(r.Device_Trust_Score || 0),
      Velocity_Score: Number(r.Velocity_Score || 0),
      Security_Awareness_Score: Number(r.Security_Awareness_Score || 0),
    }));
    riskMap = new Map();
    for (const r of riskCache) {
      riskMap.set(r.Customer_ID, r);
    }
    console.log(`[RiskProfileRepo] Loaded ${riskCache.length} risk profiles.`);
  }
}

export function getRiskProfile(customerId) {
  loadRiskProfiles();
  return riskMap.get(customerId) || null;
}
