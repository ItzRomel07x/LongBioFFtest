
from flask import Flask, request, jsonify, render_template
import requests
import urllib.parse

app = Flask(__name__)

# =========================
# CONFIG
# =========================

try:
    from config import SITE_CONFIG
    print("✓ Loaded config from config.py")
except ImportError:
    print("⚠ config.py not found, using defaults")

    SITE_CONFIG = {
        "site_name": "NEXA NATION FF BIO TOOL",
        "site_logo_emoji": "⚡",
        "freefire_version": "OB55",
        "bio_char_limit": 280,
        "default_region": "IND",
    }

app.config["SITE_CONFIG"] = SITE_CONFIG


# =========================
# ACCESS TOKEN
# =========================

def get_account_from_eat(eat_token):
    try:
        eat_token = str(eat_token).strip()

        # Full URL হলে token বের করা
        if "?" in eat_token:
            parsed = urllib.parse.urlparse(eat_token)
            params = urllib.parse.parse_qs(parsed.query)

            if params.get("access_token"):
                eat_token = params["access_token"][0]
            elif params.get("eat"):
                eat_token = params["eat"][0]

        api_url = "https://access.killersharmabot.online/access"

        response = requests.get(
            api_url,
            params={"access_token": eat_token},
            timeout=15
        )

        print("=" * 50)
        print("ACCESS API STATUS:", response.status_code)
        print("ACCESS API URL:", response.url)
        print("ACCESS API RESPONSE:", response.text[:2000])
        print("=" * 50)

        if response.status_code != 200:
            return None, None, f"Access API HTTP {response.status_code}"

        try:
            result = response.json()
        except ValueError:
            return None, None, "Access API returned invalid JSON"

        token = result.get("token")

        if not token:
            return None, None, "Access API response does not contain token"

        account = {
            "uid": str(result.get("uid", "")),
            "account_id": str(result.get("accountId", "")),
            "region": (
                result.get("lockRegion")
                or result.get("notiRegion")
                or result.get("ipRegion")
                or "IND"
            ),
            "nickname": result.get("nickname", ""),
            "server_url": result.get("serverUrl", ""),
            "level": result.get("level"),
            "platform": result.get("platform"),
            "login_platform": result.get("login_platform"),
        }

        if not account["uid"]:
            return None, None, "Access API response does not contain UID"

        return token, account, None

    except requests.exceptions.Timeout:
        return None, None, "Access API request timed out"

    except requests.exceptions.RequestException as e:
        return None, None, f"Access API request error: {e}"

    except Exception as e:
        return None, None, str(e)


# =========================
# ROUTES
# =========================

@app.route("/")
@app.route("/page")
def index():
    return render_template(
        "index.html",
        config=SITE_CONFIG
    )


# =========================
# VERIFY TOKEN
# =========================

@app.route("/api/verify-token", methods=["POST"])
def verify_token():

    try:
        data = request.get_json(silent=True) or {}

        eat_token = data.get("eat_token")

        if not eat_token:
            return jsonify({
                "success": False,
                "error": "Missing access token"
            }), 400

        token, account, error = get_account_from_eat(eat_token)

        if error:
            return jsonify({
                "success": False,
                "error": error
            }), 400

        return jsonify({
            "success": True,
            "account": account,

            # Production-এ client-এ sensitive token পাঠানো avoid করা উচিত
            "jwt_token": token
        }), 200

    except Exception as e:

        print("VERIFY ERROR:", repr(e))

        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


# =========================
# UPDATE BIO
# =========================

@app.route("/api/update-bio", methods=["POST"])
def update_bio():

    try:
        data = request.get_json(silent=True) or {}

        bio_text = data.get("bio")
        region = data.get("region")

        # -------------------------
        # Validation
        # -------------------------

        if not bio_text:
            return jsonify({
                "success": False,
                "error": "Missing bio text"
            }), 400

        bio_text = str(bio_text)

        max_chars = int(
            SITE_CONFIG.get("bio_char_limit", 280)
        )

        if len(bio_text) > max_chars:
            return jsonify({
                "success": False,
                "error": f"Bio exceeds {max_chars} characters"
            }), 400

        if not region:
            region = SITE_CONFIG.get(
                "default_region",
                "IND"
            )

        # IMPORTANT:
        # এখানে তোমার legitimate/official
        # bio-update provider/API call বসবে.
        #
        # Example:
        #
        # result = update_bio_using_official_api(
        #     bio=bio_text,
        #     region=region
        # )

        return jsonify({
            "success": False,
            "error": "Bio update provider is not configured",
            "details": {
                "region": region,
                "bio_length": len(bio_text)
            }
        }), 501

    except requests.exceptions.Timeout:
        return jsonify({
            "success": False,
            "error": "Bio update request timed out"
        }), 504

    except requests.exceptions.RequestException as e:

        print("BIO REQUEST ERROR:", repr(e))

        return jsonify({
            "success": False,
            "error": "Bio update request failed"
        }), 502

    except Exception as e:

        print("BIO UPDATE ERROR:", repr(e))

        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


# =========================
# HEALTH CHECK
# =========================

@app.route("/api/health", methods=["GET"])
def health():

    return jsonify({
        "success": True,
        "server": "online"
    }), 200


# =========================
# START
# =========================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )

