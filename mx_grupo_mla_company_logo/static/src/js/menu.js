/** @odoo-module **/

import { NavBar } from "@web/webclient/navbar/navbar";
import { patch } from "@web/core/utils/patch";
import { onMounted } from "@odoo/owl";

patch(NavBar.prototype, {
    setup() {
        super.setup();
        
        onMounted(() => {
            this._addCompanyLogo();
        });
    },

    async _addCompanyLogo() {
        try {
            // Esperar un poco para que el DOM esté completamente renderizado
            await new Promise(resolve => setTimeout(resolve, 200));
            
            const navbar = document.querySelector("nav.o_main_navbar") || 
                          document.querySelector(".o_main_navbar") ||
                          document.querySelector("nav.navbar") ||
                          document.querySelector(".navbar");
            
            if (!navbar) {
                setTimeout(() => this._addCompanyLogo(), 500);
                return;
            }
            
            // Verificar si ya existe el logo
            if (document.querySelector(".o_company_logo_custom")) {
                return;
            }
            
            // Obtener datos de la empresa actual con logo
            const companyData = await this._getCompanyDataWithLogo();
            
            if (companyData) {
                this._renderCompanyLogo(navbar, companyData);
            }
            
        } catch (error) {
            console.error("❌ Error en _addCompanyLogo:", error);
        }
    },

    async _getCompanyDataWithLogo() {
        try {
            
            // Obtener ID de la empresa actual
            let companyId = null;
            let companyName = "Mi Empresa";
            
            // Método 1: Desde this.env.services
            if (this.env && this.env.services && this.env.services.company) {
                const currentCompany = this.env.services.company.currentCompany;
                if (currentCompany && currentCompany.id) {
                    companyId = currentCompany.id;
                    companyName = currentCompany.name;
                }
            }
            
            // Método 2: Desde window.odoo si no funciona el anterior
            if (!companyId && window.odoo && window.odoo.info) {
                if (window.odoo.info.user_companies && window.odoo.info.user_companies.current_company) {
                    const [id, name] = window.odoo.info.user_companies.current_company;
                    companyId = id;
                    companyName = name;
                } else if (window.odoo.info.company_id) {
                    companyId = window.odoo.info.company_id;
                    companyName = window.odoo.info.company_name || companyName;
                }
            }
            
            if (!companyId) {
                return { id: 1, name: companyName };
            }
            
            const rpcData = await this._makeRPCCall('/web/dataset/call_kw/res.company/read', {
                model: 'res.company',
                method: 'read',
                args: [[companyId], ['id', 'name', 'logo', 'logo_web']],
                kwargs: {}
            });
            
            if (rpcData && rpcData.length > 0) {
                return rpcData[0];
            }
            
            return { id: companyId, name: companyName };
            
        } catch (error) {
            return { id: 1, name: "Mi Empresa" };
        }
    },

    async _makeRPCCall(url, params) {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'include',
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",
                    params: params,
                    id: Math.floor(Math.random() * 1000000)
                })
            });
            
            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error.message);
            }
            
            return result.result;
            
        } catch (error) {
            
            // Fallback: usar el ORM service si está disponible
            if (this.env && this.env.services && this.env.services.orm) {
                try {
                    return await this.env.services.orm.call(
                        'res.company',
                        'read',
                        [params.args[0]],
                        { fields: params.args[1] }
                    );
                } catch (ormError) {
                    console.error("❌ Error con ORM service:", ormError);
                }
            }
            
            return null;
        }
    },

    _renderCompanyLogo(navbar, companyData) {
        
        // Crear contenedor del logo
        const logoContainer = document.createElement("div");
        logoContainer.className = "o_company_logo_custom d-flex align-items-center";
        logoContainer.style.cssText = `
            margin-right: 1rem !important;
            padding-right: 1rem !important;
            border-right: 1px solid #dee2e6 !important;
            height: 100% !important;
            display: flex !important;
            align-items: center !important;
            cursor: pointer !important;
        `;
        
        // Verificar si tiene logo
        const logoField = companyData.logo_web || companyData.logo;
        
        if (logoField) {
            // Crear imagen del logo
            const logoImg = document.createElement("img");
            logoImg.src = `data:image/png;base64,${logoField}`;
            logoImg.alt = companyData.name;
            logoImg.title = companyData.name;
            logoImg.className = "o_company_logo_img";
            logoImg.style.cssText = `
                height: 32px !important;
                max-width: 120px !important;
                object-fit: contain !important;
                display: block !important;
                border-radius: 4px;
            `;
            
            // Manejar error de carga de imagen
            logoImg.onerror = () => {
                logoImg.style.display = 'none';
                const textFallback = document.createElement("span");
                textFallback.style.cssText = `
                    font-weight: 500 !important;
                    color: #0d6efd !important;
                    font-size: 0.875rem !important;
                `;
                textFallback.innerHTML = `<i class="fa fa-building me-2"></i>${companyData.name}`;
                logoContainer.appendChild(textFallback);
            };
            
            logoContainer.appendChild(logoImg);
            
        } else {
            // Crear logo de texto
            const logoText = document.createElement("div");
            logoText.className = "o_company_logo_text";
            logoText.style.cssText = `
                font-weight: 500 !important;
                color: #0d6efd !important;
                font-size: 0.875rem !important;
                display: flex !important;
                align-items: center !important;
            `;
            
            logoText.innerHTML = `
                <i class="fa fa-building me-2"></i>
                <span>${companyData.name}</span>
            `;
            
            logoContainer.appendChild(logoText);
        }
        
        // Agregar evento click para información adicional
        logoContainer.addEventListener('click', () => {
        });
        
        // Buscar el mejor lugar para insertar
        const insertionPoint = this._findInsertionPoint(navbar);
        insertionPoint.parent.insertBefore(logoContainer, insertionPoint.nextSibling);
        
        
        // Verificar que se renderizó correctamente
        setTimeout(() => {
            const addedLogo = document.querySelector(".o_company_logo_custom");
            if (addedLogo) {
                /*console.log("🔍 Verificación del logo:", {
                    visible: addedLogo.offsetParent !== null,
                    dimensions: {
                        width: addedLogo.offsetWidth,
                        height: addedLogo.offsetHeight
                    }
                });*/
            }
        }, 100);
    },

    _findInsertionPoint(navbar) {
        // Buscar diferentes puntos de inserción en orden de preferencia
        const candidates = [
            { selector: '.o_navbar_apps_menu', location: 'después del menú de apps' },
            { selector: '.breadcrumb', location: 'antes de breadcrumbs' },
            { selector: '.o_breadcrumb', location: 'antes de breadcrumbs' },
            { selector: '.navbar-nav', location: 'antes de navbar-nav' },
            { selector: '.o_main_navbar > *:first-child', location: 'después del primer elemento' }
        ];
        
        for (const candidate of candidates) {
            const element = navbar.querySelector(candidate.selector);
            if (element) {
                return {
                    parent: element.parentNode,
                    nextSibling: element.nextSibling,
                    location: candidate.location
                };
            }
        }
        
        return {
            parent: navbar,
            nextSibling: navbar.firstChild,
            location: 'principio del navbar'
        };
    }
});
