from flask import Flask, request, jsonify
from predictor_api import load_predictor

# Load the model once when the application starts
predictor = load_predictor()

app = Flask(__name__)

@app.route('/predict_price', methods=['POST'])
def predict_price_api():
    try:
        data = request.json
        cpu = data.get('cpu')
        gpu = data.get('gpu')
        brand = data.get('brand')
        ram = data.get('ram')
        ssd = data.get('ssd')

        if not all([cpu, gpu, brand, ram, ssd]):
            return jsonify({'error': 'Missing one or more required fields.'}), 400
        
        ram = int(ram)
        ssd = int(ssd)

        predicted_price = predictor.predict(cpu, gpu, brand, ram, ssd)
        
        return jsonify({
            'predicted_price': f"{predicted_price:.2f}",
            'status': 'success'
        })

    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'error': f"An unexpected error occurred: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)