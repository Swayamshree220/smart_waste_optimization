import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from datetime import datetime, timedelta

class WastePredictor:
    def __init__(self):
        self.model = GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False

    # -----------------------------------
    # Generate Synthetic Training Data
    # -----------------------------------
    def generate_training_data(self, n_bins=50, days=365):
        np.random.seed(42)
        data = []
        start_date = datetime.now() - timedelta(days=days)

        for bin_id in range(n_bins):
            base_waste = np.random.uniform(50, 200)
            weekend_factor = np.random.uniform(1.1, 1.4)

            bin_type = np.random.choice(['residential', 'commercial', 'industrial'])
            type_multiplier = {
                'residential': 1.0,
                'commercial': 1.5,
                'industrial': 2.0
            }[bin_type]

            for day in range(days):
                date = start_date + timedelta(days=day)
                day_of_week = date.weekday()
                is_weekend = 1 if day_of_week >= 5 else 0
                month = date.month

                seasonal = 1 + 0.3 * np.sin(2 * np.pi * month / 12)
                weekly = weekend_factor if is_weekend else 1.0
                noise = np.random.normal(1, 0.15)

                waste = base_waste * type_multiplier * seasonal * weekly * noise
                waste = max(0, waste)

                data.append({
                    'bin_id': bin_id,
                    'date': date,
                    'day_of_week': day_of_week,
                    'is_weekend': is_weekend,
                    'month': month,
                    'bin_type': bin_type,
                    'waste_kg': waste
                })

        return pd.DataFrame(data)

    # -----------------------------------
    # Feature Engineering
    # -----------------------------------
    def prepare_features(self, df):
        features = df.copy()

        # One-hot encode bin type
        features['bin_type_residential'] = (features['bin_type'] == 'residential').astype(int)
        features['bin_type_commercial'] = (features['bin_type'] == 'commercial').astype(int)
        features['bin_type_industrial'] = (features['bin_type'] == 'industrial').astype(int)

        # Sort for lag features
        features = features.sort_values(['bin_id', 'date'])

        for lag in [1, 7, 14]:
            features[f'waste_lag_{lag}'] = (
                features.groupby('bin_id')['waste_kg'].shift(lag)
            )

        features['waste_rolling_7'] = (
            features.groupby('bin_id')['waste_kg']
            .rolling(7)
            .mean()
            .reset_index(0, drop=True)
        )

        features['waste_rolling_30'] = (
            features.groupby('bin_id')['waste_kg']
            .rolling(30)
            .mean()
            .reset_index(0, drop=True)
        )

        # ✅ FIXED (no FutureWarning)
        features = features.bfill().fillna(0)

        feature_cols = [
            'day_of_week', 'is_weekend', 'month',
            'bin_type_residential', 'bin_type_commercial', 'bin_type_industrial',
            'waste_lag_1', 'waste_lag_7', 'waste_lag_14',
            'waste_rolling_7', 'waste_rolling_30'
        ]

        return features[feature_cols], features['waste_kg']

    # -----------------------------------
    # Train Model
    # -----------------------------------
    def train(self, df=None):
        if df is None:
            df = self.generate_training_data()

        X, y = self.prepare_features(df)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True

        return {
            'train_r2': self.model.score(X_train_scaled, y_train),
            'test_r2': self.model.score(X_test_scaled, y_test),
            'feature_importance': dict(
                zip(X.columns, self.model.feature_importances_)
            )
        }

    # -----------------------------------
    # Predict
    # -----------------------------------
    def predict(self, bin_features):
        if not self.is_trained:
            self.train()

        df = pd.DataFrame(bin_features)
        X, _ = self.prepare_features(df)
        X_scaled = self.scaler.transform(X)

        return self.model.predict(X_scaled)

    def predict_for_bins(self, bins_info, target_date=None):
        if target_date is None:
            target_date = datetime.now()

        predictions = {}
        for bin_id, info in bins_info.items():
            features = {
                'bin_id': bin_id,
                'date': target_date,
                'day_of_week': target_date.weekday(),
                'is_weekend': 1 if target_date.weekday() >= 5 else 0,
                'month': target_date.month,
                'bin_type': info['type'],
                'waste_kg': info.get('historical_avg', 100)
            }

            predictions[bin_id] = max(0, self.predict([features])[0])

        return predictions
