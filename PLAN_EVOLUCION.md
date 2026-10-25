# 🚀 Plan de Evolución — Manual Contable AI → Comunidad Contable

## Visión
Transformar Manual Contable AI de una app monousuario para una institución educativa
a una **plataforma comunitaria SaaS** donde cualquier Contador Público Certificado (CPC)
puede registrarse, crear su organización (tenant), subir su catálogo de cuentas y
generar manuales contables con IA — gratuita con opción de donativo vía Mercado Pago.

---

## 🏗️ Arquitectura Multi-Tenant

### Enfoque recomendado: **Shared Database + Tenant ID**

```
┌─────────────────────────────────────────────────┐
│                  PostgreSQL (1 BD)               │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Tenant A │  │ Tenant B │  │ Tenant C │      │
│  │ (CPC 1)  │  │ (CPC 2)  │  │ (CPC 3)  │      │
│  │          │  │          │  │          │      │
│  │ Catálogo │  │ Catálogo │  │ Catálogo │      │
│  │ Manuales │  │ Manuales │  │ Manuales │      │
│  └──────────┘  └──────────┘  └──────────┘      │
│                                                  │
│  ┌──────────────────────────────────────────┐    │
│  │     Datos compartidos (globales)         │    │
│  │  - Código Agrupador SAT (catálogo base)  │    │
│  │  - Planes de donativo                    │    │
│  └──────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

**¿Por qué este enfoque y no BDs separadas?**
- ✅ Un solo servidor PostgreSQL (menor costo)
- ✅ Migraciones sencillas (un solo esquema)
- ✅ Escalable a miles de tenants
- ✅ Código más simple de mantener
- ✅ El Código Agrupador SAT se comparte entre todos
- ✅ Aislamiento por foreign key `tenant_id` en cada modelo

---

## 📋 Fases de implementación

### FASE 1: Fundamentos Multi-Tenant + Registro de Usuarios
**Prioridad: 🔴 CRÍTICA**

#### 1.1 App `cuentas` — Sistema de usuarios y tenants
```python
# Modelo: PerfilCPC (extiende User de Django)
- usuario (OneToOne → User)
- nombre_completo
- cedula_profesional          # Cédula del CPC
- numero_certificacion        # Número de certificación ante el IMCP
- colegio_afiliado            # Colegio de Contadores al que pertenece
- especialidad                # Fiscal, Auditoría, Costos, etc.
- telefono
- ciudad
- estado
- años_experiencia
- foto_perfil
- linkedin_url
- acepta_terminos
- fecha_registro

# Modelo: Tenant (Organización/Despacho)
- nombre                      # "Despacho García y Asociados"
- rfc                         # RFC de la organización
- giro                        # Comercial, Industrial, Servicios, Educativo, etc.
- sector                      # Privado, Público, ONG, etc.
- regimen_fiscal              # Persona Moral, Física con Act. Empresarial, etc.
- direccion
- ciudad
- estado
- codigo_postal
- telefono
- logo
- propietario (FK → User)     # CPC que creó el tenant
- activo
- fecha_creacion

# Modelo: MembresíaTenant
- tenant (FK → Tenant)
- usuario (FK → User)
- rol                         # propietario, contador, auxiliar, solo_lectura
- fecha_ingreso
```

#### 1.2 Vistas de registro y onboarding
```
/registro/           → Formulario de registro CPC
/registro/tenant/    → Crear organización (paso 2)
/login/              → Inicio de sesión
/perfil/             → Editar perfil CPC
/mi-organizacion/    → Dashboard del tenant
```

### FASE 2: Catálogo de Cuentas por Tenant
**Prioridad: 🔴 CRÍTICA**

#### 2.1 Carga individual y masiva
```python
# El CodigoAgrupador SAT es GLOBAL (compartido)
# El CatalogoCuentas ahora tiene FK → Tenant

# Funcionalidades:
- Subir cuenta individual (formulario)
- Subir catálogo completo (CSV/Excel)
- Plantilla descargable de ejemplo
- Validación automática vs Código Agrupador SAT
- Importar catálogo SAT predeterminado (plantilla base)
```

#### 2.2 Formato del CSV/Excel esperado
```
cuenta | descripcion | codigo_agrupador_sat | nivel1 | nivel2 | nivel3 | nivel4
1100   | Bancos      | 102.01               | 1      | 1      |        |
1100.01| Banamex     | 102.01               | 1      | 1      | 0      | 1
```

### FASE 3: Generación de Manuales (adaptada)
**Prioridad: 🟠 IMPORTANTE**

#### 3.1 Prompt dinámico según el tenant
```python
# En vez de hardcodear "Escuela Modelo, S.C.P.", el prompt usa:
- tenant.nombre           → nombre de la organización
- tenant.giro             → contexto del giro
- tenant.regimen_fiscal   → régimen aplicable
```

### FASE 4: Donativo con Mercado Pago
**Prioridad: 🟡 DESEABLE**

#### 4.1 Integración
```python
# Modelo: Donativo
- usuario (FK → User)
- monto
- referencia_mercadopago
- estado                  # pendiente, aprobado, rechazado
- fecha

# Flujo:
1. Botón "Apoyar el proyecto" → Widget de Mercado Pago
2. Montos sugeridos: $50, $100, $200, personalizado (MXN)
3. Webhook de confirmación
4. Badge "Colaborador" en perfil
```

### FASE 5: Comunidad y Features Avanzados
**Prioridad: 🟢 FUTURO**

```
- Dashboard con estadísticas del tenant
- Exportar manuales a PDF/Word
- Compartir manuales entre colegas
- Foro/comentarios entre CPCs
- Notificaciones de cambios fiscales
- API REST para integraciones
```

---

## 🗂️ Estructura de apps Django propuesta

```
manual_contable_ai/
├── manage.py
├── manual_contable_ai/        # Settings del proyecto
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── cuentas/                   # NUEVA: Usuarios + Tenants
│   ├── models.py              # PerfilCPC, Tenant, MembresíaTenant
│   ├── views.py               # Registro, login, perfil, onboarding
│   ├── forms.py               # Formularios de registro
│   ├── admin.py
│   ├── urls.py
│   ├── middleware.py           # TenantMiddleware (inyecta tenant en request)
│   └── templates/
│       ├── registro.html
│       ├── login.html
│       ├── perfil.html
│       └── dashboard.html
│
├── catalogo/                  # MODIFICADA: Ahora multi-tenant
│   ├── models.py              # + FK tenant en CatalogoCuentas y ManualContable
│   ├── views.py               # + upload CSV/Excel, filtrado por tenant
│   ├── importador.py          # NUEVO: lógica de importación CSV/Excel
│   └── templates/
│       ├── subir_catalogo.html
│       ├── generar_manual.html
│       └── detalle_manual.html
│
├── donaciones/                # NUEVA: Mercado Pago
│   ├── models.py              # Donativo
│   ├── views.py               # Checkout, webhook
│   └── templates/
│       └── donar.html
│
└── deploy/                    # Configs de deploy (ya listo)
```

---

## 📊 Datos a recabar de los CPCs

| Campo | Obligatorio | Propósito |
|-------|-------------|-----------|
| Nombre completo | ✅ | Identificación |
| Email | ✅ | Login y comunicación |
| Cédula profesional | ✅ | Validación profesional |
| Número certificación IMCP | ❌ | Diferenciación CPC vs CP |
| Colegio afiliado | ❌ | Segmentación por colegio |
| Especialidad | ✅ | Personalización de contenido |
| Estado/Ciudad | ✅ | Segmentación geográfica |
| Años de experiencia | ❌ | Estadísticas |
| Teléfono | ❌ | Contacto directo |
| LinkedIn | ❌ | Networking profesional |
| RFC del despacho | ✅ | Tenant identification |
| Giro del despacho | ✅ | Contextualizar manuales |
| Régimen fiscal | ✅ | Contextualizar manuales |

---

## ⚠️ Decisiones que necesito de ti

1. **¿Quieres que un CPC pueda tener múltiples organizaciones (tenants)?**
   - Ej: Un contador independiente que lleva la contabilidad de 5 empresas

2. **¿Un tenant puede tener múltiples usuarios?**
   - Ej: El despacho tiene al CPC titular + 3 auxiliares contables

3. **¿Mercado Pago con montos fijos o libres?**
   - Sugeridos: $50, $100, $200, libre

4. **¿La cédula profesional del CPC es obligatoria para registrarse?**
   - O permitimos también estudiantes/auxiliares

5. **¿Empezamos por FASE 1 + 2 (core multi-tenant) y luego iteramos?**
