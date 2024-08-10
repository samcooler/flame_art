use std::net::{Ipv4Addr, SocketAddrV4, UdpSocket};

use artnet_protocol::ArtCommand;
use kiss3d::{camera::ArcBall, light::Light, scene::SceneNode, window::Window};
use nalgebra::{Point3, Translation3, UnitQuaternion, Vector3};
use rand::random;
use rosc::{OscPacket, OscType};

const ARTNET_PORT: u16 = 6454;
const OSC_PORT: u16 = 6512;

struct Face {
    center_vector: Vector3<f32>,
    normalized_center_vector: Vector3<f32>,
    fire_cone: SceneNode,
    switch: bool,
    flow: f32,
    // Rough concept of the concentration of fire. Number from 0 to 2. Poofs start out at 2 (all
    // fire concentrated around nozzle) and quickly decay to 1 (normal stable flow), then when
    // released decay to 0. Not really based in physics but it is just for the simulation.
    concentration: f32,
}
impl Face {
    pub fn new(
        vertex_indices: [usize; 4],
        vertices: &[Vector3<f32>; 32],
        parent: &mut SceneNode,
        shaft_len: f32,
        quaternion_to_rotate_5_pyramid_to_top: &UnitQuaternion<f32>,
    ) -> Self {
        let center_vector =
            // Average the vertex vectors to create the vector to the center of the face
            (vertices[vertex_indices[0]]
                + vertices[vertex_indices[1]]
                + vertices[vertex_indices[2]]
                + vertices[vertex_indices[3]])
                / 4.;
        let mut quad = parent.add_quad_with_vertices(
            vertex_indices
                .iter()
                .map(|vertex_index| Point3::<f32>::from(vertices[*vertex_index]))
                .collect::<Vec<_>>()
                .as_slice(),
            2,
            2,
        );
        quad.append_rotation(quaternion_to_rotate_5_pyramid_to_top);
        quad.set_color(random(), random(), random());
        quad.append_translation(&Translation3::new(0., shaft_len, 0.));

        let mut fire_cone = parent.add_cone(0.5, 2.);
        fire_cone.append_rotation(
            &UnitQuaternion::rotation_between(&(-Vector3::y()), &center_vector).unwrap_or_else(
                || UnitQuaternion::from_axis_angle(&Vector3::x_axis(), std::f32::consts::PI),
            ),
        );
        fire_cone.append_translation(&Translation3::from(center_vector * 1.5));
        fire_cone.append_rotation(quaternion_to_rotate_5_pyramid_to_top);
        fire_cone.append_translation(&Translation3::new(0., shaft_len, 0.));
        fire_cone.set_points_size(10.0);
        fire_cone.set_lines_width(1.0);
        fire_cone.set_surface_rendering_activation(false);
        fire_cone.set_color(1., 0.8, 0.2);

        Self {
            center_vector: quaternion_to_rotate_5_pyramid_to_top.transform_vector(&center_vector),
            normalized_center_vector: quaternion_to_rotate_5_pyramid_to_top
                .transform_vector(&center_vector)
                .normalize(),
            fire_cone,
            switch: false,
            flow: 1.,
            concentration: 1.,
        }
    }
}

fn main() {
    let c0: f32 = 5f32.sqrt() / 4.;
    let c1: f32 = (5. + 5f32.sqrt()) / 8.;
    let c2: f32 = (5. + 3. * 5f32.sqrt()) / 8.;
    let z: f32 = 0.;

    let vertices: [Vector3<f32>; 32] = [
        [c1, z, c2].into(),
        [c1, z, -c2].into(),
        [-c1, z, c2].into(),
        [-c1, z, -c2].into(),
        [c2, c1, z].into(),
        [c2, -c1, z].into(),
        [-c2, c1, z].into(),
        [-c2, -c1, z].into(),
        [z, c2, c1].into(),
        [z, c2, -c1].into(),
        [z, -c2, c1].into(),
        [z, -c2, -c1].into(),
        [z, c0, c2].into(),
        [z, c0, -c2].into(),
        [z, -c0, c2].into(),
        [z, -c0, -c2].into(),
        [c2, z, c0].into(),
        [c2, z, -c0].into(),
        [-c2, z, c0].into(),
        [-c2, z, -c0].into(),
        [c0, c2, z].into(),
        [c0, -c2, z].into(),
        [-c0, c2, z].into(),
        [-c0, -c2, z].into(),
        [c1, c1, c1].into(),
        [c1, c1, -c1].into(),
        [c1, -c1, c1].into(),
        [c1, -c1, -c1].into(),
        [-c1, c1, c1].into(),
        [-c1, c1, -c1].into(),
        [-c1, -c1, c1].into(),
        [-c1, -c1, -c1].into(),
    ];

    let mut window = Window::new("Light Curve Simulator");
    let quaternion_to_rotate_5_pyramid_to_top =
        UnitQuaternion::rotation_between(&vertices[8], &Vector3::y()).unwrap();
    let face_vertex_indices: [[usize; 4]; 30] = [
        [23, 10, 11, 21],
        [27, 11, 5, 21],
        [15, 11, 1, 27],
        [31, 11, 3, 15],
        [31, 7, 11, 23],
        [21, 10, 5, 26],
        [17, 1, 5, 27],
        [13, 3, 1, 15],
        [19, 7, 3, 31],
        [30, 10, 7, 23],
        [14, 0, 10, 26],
        [26, 0, 5, 16],
        [16, 4, 5, 17],
        [25, 1, 4, 17],
        [13, 1, 9, 25],
        [29, 3, 9, 13],
        [19, 3, 6, 29],
        [18, 7, 6, 19],
        [18, 2, 7, 30],
        [30, 2, 10, 14],
        [12, 0, 2, 14],
        [24, 4, 0, 16],
        [20, 9, 4, 25],
        [29, 9, 6, 22],
        [28, 2, 6, 18],
        [12, 8, 0, 24],
        [20, 4, 8, 24],
        [22, 9, 8, 20],
        [22, 8, 6, 28],
        [28, 8, 2, 12],
    ];

    let shaft_len = c2 * 8.;
    let mut arm = window.add_group();
    let mut faces: [Face; 30] = face_vertex_indices.map(|indices| {
        Face::new(
            indices,
            &vertices,
            &mut arm,
            shaft_len,
            &quaternion_to_rotate_5_pyramid_to_top,
        )
    });

    let mut shaft = arm.add_cylinder(c0 * 0.8, shaft_len);
    shaft.set_local_translation(Translation3::new(0., shaft_len / 2., 0.));
    shaft.set_color(0.3, 0.3, 0.3);

    window.set_light(Light::StickToCamera);

    let mut arc_ball_camera = ArcBall::new(
        Point3::new(0.0f32, shaft_len * 1.5, 10.),
        Point3::new(0.0f32, shaft_len, 0.0f32),
    );

    // Uncomment to simulate standing on the ground looking up at the sculpture
    // let mut arc_ball_camera = ArcBall::new(
    //     Point3::new(0.0f32, 0., 25.),
    //     Point3::new(0.0f32, shaft_len / 2., 0.0f32),
    // );

    let artnet_socket = create_socket(ARTNET_PORT);
    let osc_socket = create_socket(OSC_PORT);

    // Note that this gravity is referring to the vector in the space of the simulation, not the
    // exact values coming from the IMU. I.e., the simulation treats the Y axis as up while we are
    // not yet sure what axis the IMU treats as up. That conversion will be done before writing to
    // this value.
    let mut gravity = Vector3::new(0., 9.8, 0.);

    while !window.should_close() {
        window.set_framerate_limit(Some(60));
        window.render_with_camera(&mut arc_ball_camera);
        receive_artnet(&mut faces, &artnet_socket);
        receive_osc(&osc_socket, &mut gravity);
        faces.iter_mut().for_each(|face| {
            let target_concentration = 2.0 - face.flow;
            // Update concentration
            if face.switch {
                // Decay concentration to the flow value
                face.concentration =
                    face.concentration + (target_concentration - face.concentration) * 0.2;
            } else {
                // Decay concentration to zero
                face.concentration *= 0.97;
            }
            arm.set_local_rotation(
                UnitQuaternion::rotation_between(&Vector3::y(), &gravity).unwrap_or_else(|| {
                    UnitQuaternion::from_axis_angle(&Vector3::x_axis(), std::f32::consts::PI)
                }),
            );

            // Render
            let scale = 2. - face.concentration;
            let max_visible_scale = face.flow + 0.4;
            face.fire_cone.set_local_scale(scale, scale * 2., scale);
            face.fire_cone.set_local_translation(Translation3::from(
                face.center_vector + face.normalized_center_vector * scale,
            ));
            face.fire_cone
                .append_translation(&Translation3::new(0., shaft_len, 0.));

            // face.concentration - target_concentration
            // max_visible_scale - scale / ((2. - target_concentration) * 0.5)

            let color_strength = if face.switch {
                1.
            } else {
                (face.concentration / target_concentration)
                    .powi(5)
                    .clamp(0., 1.)
            };
            face.fire_cone
                .set_color(color_strength, 0.8 * color_strength, 0.2 * color_strength);
            face.fire_cone.set_visible(scale < max_visible_scale);
        });
    }
}

fn create_socket(port: u16) -> UdpSocket {
    let address = SocketAddrV4::new(Ipv4Addr::new(0, 0, 0, 0), port);
    match UdpSocket::bind(address) {
        Ok(socket) => {
            socket.set_nonblocking(true).unwrap();
            socket
        }
        Err(e) => {
            println!("Error binding to address {:?}: {:?}", address, e);
            panic!();
        }
    }
}

fn receive_osc(socket: &UdpSocket, gravity: &mut Vector3<f32>) {
    let mut inbox = [0u8; 65507];
    let Ok((received_data_len, _sender_address)) = socket.recv_from(&mut inbox) else {
        // Received nothing
        return;
    };

    let Ok((_, osc_packet)) = rosc::decoder::decode_udp(&inbox[..received_data_len]) else {
        println!("Received incorrectly formatted packet at OSC port.");
        return;
    };
    match osc_packet {
        OscPacket::Message(msg) => match (msg.addr.as_str(), msg.args.as_slice()) {
            ("/LC/gravity", [OscType::Float(x), OscType::Float(y), OscType::Float(z)]) => {
                println!("Gravity: ({}, {}, {})", x, y, z);
                gravity.x = *y;
                gravity.y = *x;
                gravity.z = -*z;
            }
            ("/LC/rotation", _) => {
                println!("Rotation");
            }
            _ => {
                println!("other OSC msg");
            }
        },
        OscPacket::Bundle(bundle) => {
            println!("OSC Bundle: {:?}", bundle);
        }
    }
}

fn receive_artnet(faces: &mut [Face; 30], socket: &UdpSocket) {
    let mut inbox = [0u8; 65507];
    let Ok((received_data_len, sender_address)) = socket.recv_from(&mut inbox) else {
        // Received nothing
        return;
    };

    match ArtCommand::from_buffer(&inbox[..received_data_len]) {
        Ok(ArtCommand::Output(output)) => {
            let data = output.data.as_ref();
            data.chunks_exact(2)
                .zip(faces.iter_mut())
                .for_each(|(bytes, face)| {
                    let new_switch = bytes[0] > 0;
                    if new_switch && !face.switch {
                        face.concentration = 2.;
                    }
                    face.switch = new_switch;
                    face.flow = bytes[1] as f32 / 255.;
                });
        }
        Err(e) => {
            println!(
                "Received bytes that aren't a valid artnet command from {:?}. Error: {:?}",
                sender_address, e
            );
        }
        _ => {
            // E.g. this will happen when the device receives its own poll message that was broadcast on the network.
            println!("Received other artnet from {:?}", sender_address);
        }
    }
}
