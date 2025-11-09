import React, { useState } from 'react';
import './App.css';

const App = () => {
  const [formData, setFormData] = useState({
    MedInc: 8.3252,
    HouseAge: 41.0,
    AveRooms: 6.984127,
    AveBedrms: 1.023810,
    Population: 322.0,
    AveOccup: 2.555556,
    Latitude: 37.88,
    Longitude: -122.23
  });
  
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: parseFloat(value) || 0
    }));
  };

  const callAPI = async (inputData) => {
    try {
      // Debug: Check what environment variables are available
      console.log('=== DEBUG: Environment Variables ===');
      console.log('VITE_MODEL_API_URL:', import.meta.env.VITE_MODEL_API_URL);
      console.log('VITE_MODEL_API_TOKEN:', import.meta.env.VITE_MODEL_API_TOKEN);
      
      // Read from OS environment variables (as set in Domino)
      const modelApiUrl = import.meta.env.VITE_MODEL_API_URL || import.meta.env.MODEL_API_URL;
      const modelApiToken = import.meta.env.VITE_MODEL_API_TOKEN || import.meta.env.MODEL_API_TOKEN;
      
      console.log('Final values - URL:', modelApiUrl, 'TOKEN:', modelApiToken ? '***SET***' : 'MISSING');
      
      if (!modelApiUrl || !modelApiToken) {
        throw new Error(`API URL or Token not configured. URL: ${modelApiUrl ? 'SET' : 'MISSING'}, TOKEN: ${modelApiToken ? 'SET' : 'MISSING'}`);
      }

      const jsonInputPayload = {
        data: [Object.values(inputData)]
      };

      const response = await fetch(modelApiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Basic ${btoa(`${modelApiToken}:${modelApiToken}`)}`
        },
        body: JSON.stringify(jsonInputPayload)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (err) {
      throw new Error(`API call failed: ${err.message}`);
    }
  };

  const handlePredict = async () => {
    setLoading(true);
    setError(null);
    setPrediction(null);

    try {
      const result = await callAPI(formData);
      setPrediction(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const inputFields = [
    { name: 'MedInc', label: 'MedInc', step: 0.0001 },
    { name: 'HouseAge', label: 'HouseAge', step: 1 },
    { name: 'AveRooms', label: 'AveRooms', step: 0.000001 },
    { name: 'AveBedrms', label: 'AveBedrms', step: 0.000001 },
    { name: 'Population', label: 'Population', step: 1 },
    { name: 'AveOccup', label: 'AveOccup', step: 0.000001 },
    { name: 'Latitude', label: 'Latitude', step: 0.01 },
    { name: 'Longitude', label: 'Longitude', step: 0.01 }
  ];

  return (
    <div className="app-container">
      <div className="app-content">
        <div className="card">
          <h1 className="title">House Price Prediction App</h1>
          
          <p className="subtitle">Enter values for the following columns:</p>

          <div className="form-grid">
            {inputFields.map((field) => (
              <div key={field.name} className="input-group">
                <label htmlFor={field.name} className="label">
                  {field.label}
                </label>
                <input
                  type="number"
                  id={field.name}
                  name={field.name}
                  value={formData[field.name]}
                  onChange={handleInputChange}
                  step={field.step}
                  className="input"
                />
              </div>
            ))}
          </div>

          <div className="button-container">
            <button
              onClick={handlePredict}
              disabled={loading}
              className="predict-button"
            >
              {loading ? 'Predicting...' : 'Predict'}
            </button>
          </div>

          {error && (
            <div className="error-box">
              <p><strong>Error:</strong> {error}</p>
            </div>
          )}

          {prediction && (
            <div className="success-box">
              <h3>API Prediction Result:</h3>
              <p>
                Predicted house price is{' '}
                <span className="price">
                  ${prediction.result?.[0]?.toFixed(2) || 'N/A'}
                </span>
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default App;