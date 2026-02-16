import './htmx.js'
import 'htmx-ext-debug/debug.js'
import 'htmx-ext-preload/preload.js'
import 'htmx-ext-alpine-morph/alpine-morph.js'
import '@fortawesome/fontawesome-free/css/all.css'
import "@fortawesome/fontawesome-free/js/all.min.js"
import '../pst/styles/sphinx-basic.css'
import '../pst/styles/pydata-sphinx-theme.scss'
import './select2/overrides.css'
import '../pst/scripts/bootstrap.js'
import '../pst/scripts/mixin.js'
import '../pst/scripts/pydata-sphinx-theme.js'
import { Toast } from 'bootstrap'
import './alpine'
// import './bootstrap'
// import 'swiper/swiper-bundle.css';
import { register } from 'swiper/element/bundle'


// register Swiper custom elements
register()

const toastElList = document.querySelectorAll('.toast')
const toastList = [...toastElList].map(toastEl => new Toast(toastEl, option))
