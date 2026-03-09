import pickle

with open("G:/MASTER/Desktop/Blender game/Python control/settings.config", "wb") as config:
    settings = dict([
        ("AutoSave", True),  # Use autosave feature
        ("SQL_host", "localhost"),
        ("SQL_user", "root"),
        ("SQL_pwd", "1234"),
        ("SSR", False),  # Screen Space Reflection
        ("Shadows", True),  # Shadows
        ("AO", True),  # Ambient Occlusion-
        ("Bloom", True),  # Glow for lights
        ("Refraction",False),  # Screen Space Refaction
        ("Soft_Shadows", False),  # Smoothen shadows
        ("MotionBlur", False),
        ("Volumetrics", False)  # Volume shading

        ])
    pickle.dump(settings, config)
