// Dropzone.js - attach to window for global access
import Dropzone from 'dropzone';

// Disable auto-discover (let user configure manually)
Dropzone.autoDiscover = false;

window.Dropzone = Dropzone;
