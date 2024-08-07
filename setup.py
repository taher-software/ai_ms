from setuptools import setup, find_packages
setup(
    name='ai_ms',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        '': ['*.txt.gz'],
    },
    install_requires=[
    'async-timeout',
    'audioread',
    'beautifulsoup4',
    'blinker',
    'boto3',
    'botocore',
    'Brotli',
    'cachetools',
    'certifi',
    'cffi',
    'charset-normalizer',
    'click',
    'crontab',
    'decorator',
    'dropbox',
    'filelock',
    'Flask',
    'Flask-Login',
    'Flask-Mail',
    'Flask-RQ2',
    'Flask-SQLAlchemy',
    'Flask-SSE',
    'freezegun',
    'fsspec',
    'ftfy',
    'google-api-core',
    'google-api-python-client',
    'google-auth',
    'google-auth-httplib2',
    'google-auth-oauthlib',
    'googleapis-common-protos',
    'greenlet',
    'httplib2',
    'huggingface-hub',
    'idna',
    'imageio',
    'itsdangerous',
    'Jinja2',
    'jmespath',
    'joblib',
    'lazy_loader',
    'librosa',
    'llvmlite',
    'MarkupSafe',
    'mpmath',
    'msgpack',
    'mutagen',
    'networkx',
    'numba',
    'numpy',
    'nvidia-cublas-cu12',
    'nvidia-cuda-cupti-cu12',
    'nvidia-cuda-nvrtc-cu12',
    'nvidia-cuda-runtime-cu12',
    'nvidia-cudnn-cu12',
    'nvidia-cufft-cu12',
    'nvidia-curand-cu12',
    'nvidia-cusolver-cu12',
    'nvidia-cusparse-cu12',
    'nvidia-nccl-cu12',
    'nvidia-nvjitlink-cu12',
    'nvidia-nvtx-cu12',
    'oauthlib',
    'onetimepass',
    'open_clip_torch',
    'openai-clip',
    'opencv-python',
    'packaging',
    'pillow',
    'platformdirs',
    'ply',
    'pooch',
    'proto-plus',
    'protobuf',
    'pyasn1',
    'pyasn1_modules',
    'pycparser',
    'pycryptodomex',
    'PyJWT',
    'pyparsing',
    'python-dateutil',
    'PyYAML',
    'redis',
    'regex',
    'requests',
    'requests-oauthlib',
    'rq',
    'rq-scheduler',
    'rsa',
    's3transfer',
    'safetensors',
    'scikit-learn',
    'scipy',
    'sentence-transformers',
    'six',
    'soundfile',
    'soupsieve',
    'soxr',
    'SQLAlchemy',
    'stone',
    'sympy',
    'threadpoolctl',
    'timm',
    'tokenizers',
    'torch',
    'torchlibrosa',
    'torchvision',
    'tqdm',
    'transformers',
    'triton',
    'typing_extensions',
    'uritemplate',
    'urllib3',
    'wcwidth',
    'websockets',
    'Werkzeug',
    'yt-dlp',
    'python-ffmpeg-video-streaming',
    'pycaption',
    'sendgrid',
    'moviepy'
    
    ]
),